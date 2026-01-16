#!/usr/bin/env python3
"""
triage_evidence_upgrade.py - re-score evidence (E, H) using full text

input: articles with fulltext_ok=1 but E<=2
action: run skeptic on methods + figure captions
output: updated E, H, frontier_flag, route
"""

import argparse
import json
import hashlib
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import fitz  # PyMuPDF

# config
OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_SKEPTIC = "gemma2:9b"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "llm"
DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"


EVIDENCE_PROMPT = """You are a skeptical evidence reviewer for a science education platform.

Given the METHODS section and FIGURE CAPTIONS from a research paper, re-assess the evidence strength.

**E - Evidence Strength (0-5)**
- 0: assertion-heavy, unclear methods
- 1: minimal baselines; weak controls
- 2: some baselines; limited uncertainty; plausible but fragile
- 3: solid baseline comparisons + uncertainty reporting
- 4: ablations/sensitivity/replication across datasets or conditions
- 5: multiple independent validations

**H - Hype Risk (0-5)**
- 0: cautious, bounded claims; limitations explicit
- 1: minor PR tone, still grounded
- 2: some overreach; mostly defensible
- 3: strong claims with partial support
- 4: "breakthrough" language + thin controls
- 5: viral-weak: big claim, low evidence

Look for:
- Controls and baselines mentioned?
- Error bars / uncertainty quantified?
- Multiple conditions tested?
- Limitations acknowledged?
- Claims proportional to evidence?

METHODS SECTION:
{methods}

FIGURE CAPTIONS:
{figures}

Return ONLY valid JSON:
{{
  "E": <int 0-5>,
  "H": <int 0-5>,
  "evidence_notes": "<brief explanation of evidence assessment>",
  "concerns": ["<concern1>", "<concern2>"] or [],
  "confidence": <float 0-1>
}}
"""


def extract_pdf_sections(pdf_path: str) -> Dict[str, str]:
    """extract methods section and figure captions from PDF"""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        # simple heuristic extraction
        text_lower = full_text.lower()

        # find methods section
        methods = ""
        methods_patterns = [
            (r"methods", r"results"),
            (r"materials and methods", r"results"),
            (r"experimental", r"results"),
            (r"methodology", r"results"),
        ]

        for start_pat, end_pat in methods_patterns:
            start_idx = text_lower.find(start_pat)
            if start_idx != -1:
                end_idx = text_lower.find(end_pat, start_idx + 100)
                if end_idx != -1:
                    methods = full_text[start_idx:end_idx][:5000]  # limit length
                    break
                else:
                    methods = full_text[start_idx:start_idx + 5000]
                    break

        if not methods:
            methods = "Methods section not clearly identified."

        # find figure captions
        import re
        figures = ""
        fig_patterns = [
            r"(Fig\.?\s*\d+[.:]\s*[^\n]+(?:\n[^\n]+)?)",
            r"(Figure\s*\d+[.:]\s*[^\n]+(?:\n[^\n]+)?)",
        ]

        for pattern in fig_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                figures = "\n\n".join(matches[:10])  # first 10 figures
                break

        if not figures:
            figures = "Figure captions not clearly identified."

        return {"methods": methods, "figures": figures}

    except Exception as e:
        return {"methods": f"Error extracting: {e}", "figures": ""}


def cache_key(model: str, role: str, prompt: str) -> str:
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
    return f"{model}_{role}_{prompt_hash}"


def load_cache(key: str) -> Optional[Dict]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None


def save_cache(key: str, data: Dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    cache_file.write_text(json.dumps(data, indent=2))


def call_ollama(prompt: str, model: str) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048, "num_ctx": 16384}
    }
    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=300)
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "")


def extract_json(text: str) -> Optional[Dict]:
    import re
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    patterns = [r"```json\s*([\s\S]*?)\s*```", r"```\s*([\s\S]*?)\s*```", r"\{[\s\S]*\}"]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                json_str = match.group(1) if "```" in pattern else match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
    return None


def compute_route(S: int, E: int, T: int, M: int, H: int) -> tuple:
    """compute routing based on scores"""
    frontier = False

    if T <= 1 or (H >= 4 and E <= 3):
        return "reject", frontier

    if E >= 4 and T >= 4 and (S >= 4 or M >= 4) and H <= 2:
        return "indepth", frontier

    if E >= 3 and T >= 3 and (S >= 3 or M >= 3) and H <= 3:
        return "digest", frontier

    if T >= 2 and (S >= 3 or M >= 3):
        if E <= 2:
            frontier = True
        return "blurb", frontier

    return "reject", frontier


def upgrade_evidence(article_url: str, pdf_path: str, current_scores: Dict, conn: sqlite3.Connection) -> Dict:
    """re-score evidence using full text"""
    print(f"\n>>> upgrading: {article_url[:50]}...")

    # extract sections
    sections = extract_pdf_sections(pdf_path)
    print(f"  methods: {len(sections['methods'])} chars")
    print(f"  figures: {len(sections['figures'])} chars")

    # build prompt
    prompt = EVIDENCE_PROMPT.format(
        methods=sections["methods"][:4000],
        figures=sections["figures"][:2000]
    )

    # check cache
    key = cache_key(MODEL_SKEPTIC, "evidence_upgrade", prompt)
    cached = load_cache(key)
    if cached:
        print(f"  [skeptic] using cached response")
        result = cached
    else:
        print(f"  [skeptic] calling {MODEL_SKEPTIC}...")
        raw = call_ollama(prompt, MODEL_SKEPTIC)
        result = extract_json(raw)
        if result:
            save_cache(key, result)
        else:
            print(f"  [skeptic] failed to parse JSON")
            return {"status": "error", "error_msg": "JSON parse failed"}

    # get new scores
    new_E = result.get("E", current_scores.get("E", 0))
    new_H = result.get("H", current_scores.get("H", 0))

    print(f"  E: {current_scores.get('E', 0)} -> {new_E}")
    print(f"  H: {current_scores.get('H', 0)} -> {new_H}")

    # recompute route
    S = current_scores.get("S", 0)
    T = current_scores.get("T", 0)
    M = current_scores.get("M", 0)
    new_route, new_frontier = compute_route(S, new_E, T, M, new_H)

    print(f"  route: {new_route} {'(frontier)' if new_frontier else ''}")

    # update DB
    conn.execute("""
        UPDATE triage_result
        SET score_e = ?,
            score_h = ?,
            route = ?,
            frontier_flag = ?
        WHERE article_url = ?
    """, (new_E, new_H, new_route, 1 if new_frontier else 0, article_url))
    conn.commit()

    return {
        "status": "ok",
        "E": new_E,
        "H": new_H,
        "route": new_route,
        "frontier": new_frontier,
        "notes": result.get("evidence_notes", ""),
        "concerns": result.get("concerns", [])
    }


def run_evidence_upgrade(limit: int = 10, dry_run: bool = False) -> Dict:
    """upgrade evidence scores for articles with fulltext"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # get candidates: articles with confirmed OA PDF and low E
    cursor = conn.execute("""
        SELECT article_url, fulltext_path, score_s, score_e, score_t, score_m, score_h
        FROM triage_result
        WHERE fulltext_ok = 1
          AND access_state = 'oa_pdf_found'
          AND score_e <= 2
          AND status = 'ok'
        LIMIT ?
    """, (limit,))

    articles = cursor.fetchall()
    print(f"=== EVIDENCE UPGRADE ===")
    print(f"found {len(articles)} articles needing evidence upgrade")

    results = {"upgraded": 0, "errors": 0}

    for article in articles:
        if dry_run:
            print(f"[dry-run] would upgrade: {article['article_url'][:50]}...")
            continue

        current_scores = {
            "S": article["score_s"],
            "E": article["score_e"],
            "T": article["score_t"],
            "M": article["score_m"],
            "H": article["score_h"]
        }

        try:
            result = upgrade_evidence(
                article["article_url"],
                article["fulltext_path"],
                current_scores,
                conn
            )
            if result.get("status") == "ok":
                results["upgraded"] += 1
            else:
                results["errors"] += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            results["errors"] += 1

    conn.close()

    print(f"\n=== SUMMARY ===")
    print(f"upgraded: {results['upgraded']}")
    print(f"errors: {results['errors']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="upgrade evidence scores using full text")
    parser.add_argument("--limit", type=int, default=10, help="max articles to process")
    parser.add_argument("--dry-run", action="store_true", help="don't actually call models")

    args = parser.parse_args()
    run_evidence_upgrade(args.limit, args.dry_run)


if __name__ == "__main__":
    main()
