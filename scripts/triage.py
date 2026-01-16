#!/usr/bin/env python3
"""
triage.py - 2-model committee for article intake scoring

models:
- builder (qwen3:latest): generates S,E,T,M,H scores + TLDR
- skeptic (gemma2:9b): challenges scores, especially E and H

routing rules:
- indepth: E>=4 AND T>=4 AND (S>=4 OR M>=4) AND H<=2
- digest:  E>=3 AND T>=3 AND (S>=3 OR M>=3) AND H<=3
- blurb:   T>=2 AND (S>=3 OR M>=3); if E<=2 -> frontier_flag=1
- reject:  T<=1 OR (H>=4 AND E<=3)
"""

import argparse
import json
import hashlib
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

# config
OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_BUILDER = "qwen3:latest"
MODEL_SKEPTIC = "gemma2:9b"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "llm"
DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"


# === prompts ===

BUILDER_PROMPT = """You are a research paper evaluator for an undergraduate science education platform.

Given an article's headline and teaser, score it on these dimensions (0-5 each):

**S - Scientific Significance (0-5)**
How much does this change what becomes feasible/believed?
- 0: trivial increment
- 3: removes common bottleneck or strong new dataset/method
- 5: field-shifting (rare)

**E - Evidence Strength (0-5)**
How well is the central claim supported?
- 0: assertion-heavy, unclear methods
- 3: solid baseline comparisons + uncertainty reporting
- 5: multiple independent validations

**T - Teachability (0-5)**
Can an undergrad learn something real from it?
- 0: requires specialist background
- 3: explainable with standard UG prerequisites
- 5: multiple course hooks + clean mental model

**M - Media Affordance (0-5)**
Can you produce diagrams/audio/quizzes cheaply?
- 0: no clean figure/object
- 3: one pivot figure + one concept diagram possible
- 5: perfect 'story object'

**H - Hype Risk (0-5)**
How likely the headline overstates what evidence supports?
- 0: cautious, bounded claims
- 3: strong claims with partial support
- 5: viral-weak: big claim, low evidence

Also provide:
- tldr: 1-2 sentence summary for students
- pivot_figure: description of one visual that could anchor understanding
- course_hooks: list of 1-3 relevant undergraduate courses

ARTICLE:
Headline: {headline}
Teaser: {teaser}
Source: {source}
Discipline: {discipline}

Return ONLY valid JSON:
{{
  "S": <int 0-5>,
  "E": <int 0-5>,
  "T": <int 0-5>,
  "M": <int 0-5>,
  "H": <int 0-5>,
  "tldr": "<string>",
  "pivot_figure": "<string>",
  "course_hooks": ["<course1>", "<course2>"]
}}
"""

SKEPTIC_PROMPT = """You are a skeptical reviewer checking another model's evaluation of a research article.

Your job is to challenge the scores, especially:
- E (Evidence): Is the evidence actually strong? Look for missing controls, weak baselines, overstated results.
- H (Hype): Is the headline/teaser making claims beyond what's supported?

ORIGINAL ARTICLE:
Headline: {headline}
Teaser: {teaser}

BUILDER'S SCORES:
{builder_json}

Review critically. If you disagree with any score by 2+ points, explain why.
Return your adjusted scores (or same if you agree) with brief justifications.

Return ONLY valid JSON:
{{
  "S": <int 0-5>,
  "E": <int 0-5>,
  "T": <int 0-5>,
  "M": <int 0-5>,
  "H": <int 0-5>,
  "adjustments": {{
    "E": "<why adjusted or 'agree'>",
    "H": "<why adjusted or 'agree'>"
  }},
  "confidence": <float 0-1>
}}
"""


# === utilities ===

def cache_key(model: str, role: str, prompt: str) -> str:
    """generate cache key from model + role + prompt hash"""
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
    return f"{model}_{role}_{prompt_hash}"


def load_cache(key: str) -> Optional[Dict]:
    """load cached response if exists"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None


def save_cache(key: str, data: Dict) -> None:
    """save response to cache"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    cache_file.write_text(json.dumps(data, indent=2))


def call_ollama(prompt: str, model: str, temperature: float = 0.3) -> str:
    """call ollama and return raw response"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 2048,
            "num_ctx": 8192
        }
    }
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=300
    )
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "")


def extract_json(text: str) -> Optional[Dict]:
    """extract json from response"""
    import re
    # try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # try to find json block
    patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"\{[\s\S]*\}"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                json_str = match.group(1) if "```" in pattern else match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
    return None


# === triage logic ===

def run_builder(article: Dict) -> Dict:
    """run builder model to generate initial scores"""
    prompt = BUILDER_PROMPT.format(
        headline=article.get("headline", ""),
        teaser=article.get("teaser", ""),
        source=article.get("source", ""),
        discipline=article.get("discipline", "")
    )

    key = cache_key(MODEL_BUILDER, "builder", prompt)
    cached = load_cache(key)
    if cached:
        print(f"  [builder] using cached response")
        return cached

    print(f"  [builder] calling {MODEL_BUILDER}...")
    raw = call_ollama(prompt, MODEL_BUILDER)
    result = extract_json(raw)

    if result:
        save_cache(key, result)
        return result
    else:
        print(f"  [builder] failed to parse JSON")
        return {}


def run_skeptic(article: Dict, builder_result: Dict) -> Dict:
    """run skeptic model to challenge scores"""
    prompt = SKEPTIC_PROMPT.format(
        headline=article.get("headline", ""),
        teaser=article.get("teaser", ""),
        builder_json=json.dumps(builder_result, indent=2)
    )

    key = cache_key(MODEL_SKEPTIC, "skeptic", prompt)
    cached = load_cache(key)
    if cached:
        print(f"  [skeptic] using cached response")
        return cached

    print(f"  [skeptic] calling {MODEL_SKEPTIC}...")
    raw = call_ollama(prompt, MODEL_SKEPTIC)
    result = extract_json(raw)

    if result:
        save_cache(key, result)
        return result
    else:
        print(f"  [skeptic] failed to parse JSON")
        return {}


def merge_scores(builder: Dict, skeptic: Dict) -> Dict:
    """merge builder and skeptic scores, preferring skeptic for E and H"""
    result = {
        "S": builder.get("S", 0),
        "E": skeptic.get("E", builder.get("E", 0)),  # prefer skeptic
        "T": builder.get("T", 0),
        "M": builder.get("M", 0),
        "H": skeptic.get("H", builder.get("H", 0)),  # prefer skeptic
        "tldr": builder.get("tldr", ""),
        "pivot_figure": builder.get("pivot_figure", ""),
        "course_hooks": builder.get("course_hooks", []),
        "skeptic_adjustments": skeptic.get("adjustments", {}),
        "confidence": skeptic.get("confidence", 0.5)
    }
    return result


def compute_route(scores: Dict) -> tuple:
    """compute routing based on S,E,T,M,H scores"""
    S = scores.get("S", 0)
    E = scores.get("E", 0)
    T = scores.get("T", 0)
    M = scores.get("M", 0)
    H = scores.get("H", 0)

    frontier = False

    # reject first
    if T <= 1 or (H >= 4 and E <= 3):
        return "reject", frontier

    # indepth: E>=4 AND T>=4 AND (S>=4 OR M>=4) AND H<=2
    if E >= 4 and T >= 4 and (S >= 4 or M >= 4) and H <= 2:
        return "indepth", frontier

    # digest: E>=3 AND T>=3 AND (S>=3 OR M>=3) AND H<=3
    if E >= 3 and T >= 3 and (S >= 3 or M >= 3) and H <= 3:
        return "digest", frontier

    # blurb: T>=2 AND (S>=3 OR M>=3)
    if T >= 2 and (S >= 3 or M >= 3):
        if E <= 2:
            frontier = True  # label as frontier/early
        return "blurb", frontier

    return "reject", frontier


def triage_article(article: Dict, run_id: str, conn: sqlite3.Connection) -> Dict:
    """run full triage on one article"""
    url = article.get("url", "")
    print(f"\n>>> triaging: {article.get('headline', '')[:60]}...")

    # step 1: builder
    builder_result = run_builder(article)
    if not builder_result:
        return {"status": "error", "error_msg": "builder failed"}

    # save builder vote
    conn.execute("""
        INSERT INTO model_vote (run_id, article_url, role, model_name, json_output)
        VALUES (?, ?, 'builder', ?, ?)
    """, (run_id, url, MODEL_BUILDER, json.dumps(builder_result)))

    # step 2: skeptic
    skeptic_result = run_skeptic(article, builder_result)
    if not skeptic_result:
        # fallback to builder scores
        skeptic_result = builder_result

    # save skeptic vote
    conn.execute("""
        INSERT INTO model_vote (run_id, article_url, role, model_name, json_output)
        VALUES (?, ?, 'skeptic', ?, ?)
    """, (run_id, url, MODEL_SKEPTIC, json.dumps(skeptic_result)))

    # step 3: merge
    merged = merge_scores(builder_result, skeptic_result)

    # step 4: route
    route, frontier = compute_route(merged)

    # step 5: write triage_result
    conn.execute("""
        INSERT OR REPLACE INTO triage_result
        (run_id, article_url, discipline, score_s, score_e, score_t, score_m, score_h,
         route, frontier_flag, tldr, pivot_figure_prompt, course_hooks_json, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ok')
    """, (
        run_id, url, article.get("discipline"),
        merged.get("S", 0), merged.get("E", 0), merged.get("T", 0),
        merged.get("M", 0), merged.get("H", 0),
        route, 1 if frontier else 0,
        merged.get("tldr", ""),
        merged.get("pivot_figure", ""),
        json.dumps(merged.get("course_hooks", []))
    ))

    conn.commit()

    print(f"  scores: S={merged['S']} E={merged['E']} T={merged['T']} M={merged['M']} H={merged['H']}")
    print(f"  route: {route} {'(frontier)' if frontier else ''}")

    return {
        "status": "ok",
        "route": route,
        "frontier": frontier,
        "scores": merged
    }


def run_triage(week: str, disciplines: List[str], limit: int = 10, dry_run: bool = False) -> Dict:
    """run triage for a week"""
    conn = sqlite3.connect(DB_PATH)

    # ensure schema exists
    from db_schema_triage import ensure_triage_schema
    ensure_triage_schema(conn)

    # create run
    run_id = f"triage_{week}_{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO triage_run (run_id, week_of, model_builder, model_skeptic)
        VALUES (?, ?, ?, ?)
    """, (run_id, week, MODEL_BUILDER, MODEL_SKEPTIC))
    conn.commit()

    print(f"=== TRIAGE RUN {run_id} ===")
    print(f"week: {week}")
    print(f"disciplines: {disciplines}")

    # get pending articles
    placeholders = ",".join("?" * len(disciplines))
    query = f"""
        SELECT url, headline, teaser, source, discipline
        FROM archive
        WHERE discipline IN ({placeholders})
        ORDER BY approved_date DESC
        LIMIT ?
    """
    cursor = conn.execute(query, disciplines + [limit])
    articles = [
        {"url": r[0], "headline": r[1], "teaser": r[2], "source": r[3], "discipline": r[4]}
        for r in cursor.fetchall()
    ]

    print(f"found {len(articles)} articles to triage")

    results = {"indepth": [], "digest": [], "blurb": [], "reject": []}

    for article in articles:
        if dry_run:
            print(f"[dry-run] would triage: {article['headline'][:50]}...")
            continue

        result = triage_article(article, run_id, conn)
        if result.get("status") == "ok":
            route = result.get("route", "reject")
            results[route].append(article["url"])

    conn.close()

    # summary
    print(f"\n=== SUMMARY ===")
    for route, urls in results.items():
        print(f"{route}: {len(urls)}")

    return results


def main():
    parser = argparse.ArgumentParser(description="triage articles for TheBeakers")
    parser.add_argument("--week", default=datetime.now().strftime("%Y-%m-%d"),
                        help="week to process (YYYY-MM-DD)")
    parser.add_argument("--disciplines", default="chemistry,physics,biology",
                        help="comma-separated list of disciplines")
    parser.add_argument("--limit", type=int, default=10,
                        help="max articles to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="don't actually call models")

    args = parser.parse_args()
    disciplines = [d.strip() for d in args.disciplines.split(",")]

    run_triage(args.week, disciplines, args.limit, args.dry_run)


if __name__ == "__main__":
    main()
