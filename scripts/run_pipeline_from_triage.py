#!/usr/bin/env python3
"""
run_pipeline_from_triage.py - run full pipeline on triaged articles

gates on:
- route in ('indepth', 'digest') OR
- route='blurb' AND frontier_flag=0 (promoted after evidence upgrade)

skips:
- route='reject'
- route='blurb' AND frontier_flag=1 (still needs evidence upgrade)
- articles without fulltext_ok=1
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# paths
DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
OUTPUT_BASE = Path(__file__).parent.parent / "data" / "stories"
PIPELINE_SCRIPT = Path("/home/kiran/.claude/skills/story-renderer/scripts/run_stage.py")


def get_pipeline_candidates(conn: sqlite3.Connection, limit: int = 5) -> List[Dict]:
    """get articles ready for pipeline processing

    requires:
    - access_state = 'oa_pdf_found' (confirmed OA PDF)
    - route in ('indepth', 'digest') OR promoted blurb (frontier_flag=0)
    """
    cursor = conn.execute("""
        SELECT
            article_url,
            discipline,
            route,
            frontier_flag,
            fulltext_path,
            tldr,
            score_s, score_e, score_t, score_m, score_h
        FROM triage_result
        WHERE status = 'ok'
          AND fulltext_ok = 1
          AND access_state = 'oa_pdf_found'
          AND (
              route IN ('indepth', 'digest')
              OR (route = 'blurb' AND frontier_flag = 0)
          )
        ORDER BY
            CASE route
                WHEN 'indepth' THEN 1
                WHEN 'digest' THEN 2
                WHEN 'blurb' THEN 3
            END,
            score_s DESC, score_t DESC
        LIMIT ?
    """, (limit,))

    articles = []
    for row in cursor.fetchall():
        articles.append({
            "url": row[0],
            "discipline": row[1],
            "route": row[2],
            "frontier": row[3],
            "fulltext_path": row[4],
            "tldr": row[5],
            "scores": {
                "S": row[6], "E": row[7], "T": row[8], "M": row[9], "H": row[10]
            }
        })

    return articles


def article_id_from_url(url: str) -> str:
    """generate safe directory name from URL"""
    import re
    import hashlib

    doi_match = re.search(r'10\.\d{4,}/[^\s]+', url)
    if doi_match:
        doi = doi_match.group(0)
        doi = re.sub(r'[?#].*$', '', doi)
        return doi.replace('/', '_').replace(':', '_')
    return hashlib.md5(url.encode()).hexdigest()[:16]


def extract_text_from_pdf(pdf_path: str) -> str:
    """extract text from PDF for Stage 1"""
    import fitz

    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"  error extracting PDF: {e}")
        return ""


def run_pipeline_stage(stage: int, input_path: Path, output_dir: Path, model: str) -> bool:
    """run a single pipeline stage"""
    cmd = [
        sys.executable, str(PIPELINE_SCRIPT),
        str(stage),
        "--input", str(input_path),
        "--output-dir", str(output_dir),
        "--model", model
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            return True
        else:
            print(f"  stage {stage} failed: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  stage {stage} timed out")
        return False
    except Exception as e:
        print(f"  stage {stage} error: {e}")
        return False


def process_article(article: Dict, model: str, dry_run: bool = False) -> Dict:
    """run full pipeline on one article"""
    url = article["url"]
    article_id = article_id_from_url(url)
    output_dir = OUTPUT_BASE / article["discipline"] / article_id

    print(f"\n>>> processing: {url[:60]}...")
    print(f"    route: {article['route']}, scores: S={article['scores']['S']} E={article['scores']['E']} T={article['scores']['T']}")
    print(f"    output: {output_dir}")

    if dry_run:
        print("  [dry-run] would process")
        return {"status": "dry-run"}

    output_dir.mkdir(parents=True, exist_ok=True)

    # step 1: extract text from PDF
    pdf_path = article.get("fulltext_path")
    if not pdf_path or not Path(pdf_path).exists():
        print(f"  error: no PDF at {pdf_path}")
        return {"status": "error", "error": "no PDF"}

    text = extract_text_from_pdf(pdf_path)
    if not text or len(text) < 1000:
        print(f"  error: PDF extraction failed or too short ({len(text)} chars)")
        return {"status": "error", "error": "extraction failed"}

    # save source.md
    source_path = output_dir / "source.md"
    source_path.write_text(text, encoding="utf-8")
    print(f"  extracted {len(text)} chars to source.md")

    # run stages 1-4
    stages_ok = True
    current_input = source_path

    for stage in [1, 2, 3, 4]:
        print(f"  running stage {stage}...")

        if stage == 1:
            input_path = current_input
        else:
            # stages 2-4 read from story-data.json
            input_path = output_dir / "story-data.json"
            if not input_path.exists():
                print(f"  error: no story-data.json for stage {stage}")
                stages_ok = False
                break

        success = run_pipeline_stage(stage, input_path, output_dir, model)
        if not success:
            stages_ok = False
            break

    if stages_ok:
        print(f"  SUCCESS: all stages complete")
        return {"status": "ok", "output_dir": str(output_dir)}
    else:
        print(f"  FAILED: pipeline stopped")
        return {"status": "error", "error": "pipeline failed"}


def run_pipeline_batch(limit: int = 5, model: str = "qwen3:latest", dry_run: bool = False) -> Dict:
    """run pipeline on batch of triaged articles"""
    conn = sqlite3.connect(DB_PATH)

    articles = get_pipeline_candidates(conn, limit)
    print(f"=== PIPELINE BATCH ===")
    print(f"found {len(articles)} articles ready for processing")
    print(f"model: {model}")

    results = {"processed": 0, "errors": 0}

    for article in articles:
        result = process_article(article, model, dry_run)
        if result.get("status") == "ok":
            results["processed"] += 1
        elif result.get("status") != "dry-run":
            results["errors"] += 1

    conn.close()

    print(f"\n=== SUMMARY ===")
    print(f"processed: {results['processed']}")
    print(f"errors: {results['errors']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="run pipeline on triaged articles")
    parser.add_argument("--limit", type=int, default=5, help="max articles to process")
    parser.add_argument("--model", default="qwen3:latest", help="ollama model")
    parser.add_argument("--dry-run", action="store_true", help="don't actually process")

    args = parser.parse_args()
    run_pipeline_batch(args.limit, args.model, args.dry_run)


if __name__ == "__main__":
    main()
