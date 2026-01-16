#!/usr/bin/env python3
"""
curriculum_pipeline.py - end-to-end pipeline for curriculum-connected articles

ties together:
- society_fetcher.py: fetch papers from society journals
- curriculum_matcher.py: match papers to curriculum topics
- quiz_generator.py: generate quizzes for matched topics

produces a complete article package with curriculum connection and quizzes.

usage:
    python curriculum_pipeline.py chemistry           # process one discipline
    python curriculum_pipeline.py --all               # process all disciplines
    python curriculum_pipeline.py --status            # show pipeline status
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# import sibling modules
SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from society_fetcher import (
    Paper, fetch_discipline, save_to_db, SOURCES, DB_PATH
)
from curriculum_matcher import (
    match_paper, get_qdrant_client, load_curriculum
)
from quiz_generator import (
    generate_for_topic, get_all_topics
)

# output paths
OUTPUT_DIR = PROJECT_DIR / "data" / "pipeline_output"
QUIZ_COLLECTION = "quizzes_questions"


def ensure_output_dir():
    """create output directory if needed"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_pipeline_status() -> Dict:
    """get current pipeline status"""

    status = {
        "papers": 0,
        "papers_by_discipline": {},
        "papers_with_curriculum": 0,
        "quizzes": 0,
        "quizzes_by_discipline": {},
    }

    # count papers
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM society_papers")
        status["papers"] = cur.fetchone()[0]

        cur.execute("SELECT discipline, COUNT(*) FROM society_papers GROUP BY discipline")
        for row in cur.fetchall():
            status["papers_by_discipline"][row[0]] = row[1]

        cur.execute("SELECT COUNT(*) FROM society_papers WHERE curriculum_topics IS NOT NULL AND curriculum_topics != '[]'")
        status["papers_with_curriculum"] = cur.fetchone()[0]

        conn.close()

    # count quizzes
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://localhost:6333")
        info = client.get_collection(QUIZ_COLLECTION)
        status["quizzes"] = info.points_count

        # count by discipline
        results = client.scroll(
            collection_name=QUIZ_COLLECTION,
            limit=10000,
            with_payload=True,
        )
        for point in results[0]:
            disc = point.payload.get("discipline", "unknown")
            status["quizzes_by_discipline"][disc] = status["quizzes_by_discipline"].get(disc, 0) + 1
    except:
        pass

    return status


def print_status():
    """print pipeline status"""

    status = get_pipeline_status()

    print("\n=== CURRICULUM PIPELINE STATUS ===\n")

    print(f"Papers collected: {status['papers']}")
    for disc, count in sorted(status['papers_by_discipline'].items()):
        print(f"  {disc}: {count}")

    print(f"\nPapers with curriculum match: {status['papers_with_curriculum']}")

    print(f"\nQuiz questions: {status['quizzes']}")
    for disc, count in sorted(status['quizzes_by_discipline'].items()):
        print(f"  {disc}: {count}")


def process_discipline(discipline: str, generate_quizzes: bool = True, verbose: bool = True) -> Dict:
    """process a single discipline through the pipeline"""

    result = {
        "discipline": discipline,
        "papers_fetched": 0,
        "papers_matched": 0,
        "quizzes_generated": 0,
        "errors": [],
    }

    if verbose:
        print(f"\n=== PROCESSING: {discipline.upper()} ===")

    # step 1: fetch papers
    if verbose:
        print("\n[1/3] Fetching papers from society journals...")

    try:
        papers = fetch_discipline(discipline, download_pdfs=False)
        result["papers_fetched"] = len(papers)

        # save to database
        if papers:
            save_to_db(papers)
            if verbose:
                print(f"  fetched and saved {len(papers)} papers")
    except Exception as e:
        result["errors"].append(f"fetch error: {e}")
        if verbose:
            print(f"  [!] fetch error: {e}")

    # step 2: match curriculum
    if verbose:
        print("\n[2/3] Matching papers to curriculum...")

    matched_papers = []
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            SELECT doi, title, abstract FROM society_papers
            WHERE discipline = ? AND (curriculum_topics IS NULL OR curriculum_topics = '[]')
            ORDER BY created_at DESC LIMIT 10
        """, (discipline,))

        for row in cur.fetchall():
            doi, title, abstract = row
            try:
                match_result = match_paper(title, abstract or "", discipline)
                connection = match_result["connection"]

                if connection["related_topics"] or connection["prerequisites"]:
                    matched_papers.append({
                        "doi": doi,
                        "title": title,
                        "connection": connection,
                        "html": match_result["html"],
                    })

                    # update database with curriculum info
                    topics = [t["topic"] for t in connection["matched_topics"]]
                    cur.execute("""
                        UPDATE society_papers
                        SET curriculum_topics = ?
                        WHERE doi = ?
                    """, (json.dumps(topics), doi))

                    if verbose:
                        print(f"  matched: {title[:50]}...")
                        print(f"    topics: {', '.join(topics[:3])}")

            except Exception as e:
                result["errors"].append(f"match error for {doi}: {e}")

        conn.commit()
        conn.close()

    result["papers_matched"] = len(matched_papers)

    # step 3: generate quizzes for matched topics
    if generate_quizzes and matched_papers:
        if verbose:
            print("\n[3/3] Generating quizzes for matched topics...")

        curriculum = load_curriculum()
        client = get_qdrant_client()

        # collect unique topics from matched papers
        topics_to_generate = set()
        for paper in matched_papers:
            for topic in paper["connection"].get("matched_topics", []):
                topic_slug = topic.get("topic", "").lower().replace(" ", "-").replace("&", "and")
                topics_to_generate.add((discipline, topic.get("subfield", ""), topic_slug))

        for disc, subfield, topic_slug in topics_to_generate:
            # find the topic in curriculum
            disc_data = curriculum.get(disc, {})
            for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
                for topic in subfield_data.get("topics", []):
                    if topic["slug"] == topic_slug or topic_slug in topic["name"].lower():
                        try:
                            count = generate_for_topic(
                                client, disc, subfield_name,
                                subfield_data.get("difficulty", "sophomore"),
                                topic, verbose=verbose
                            )
                            result["quizzes_generated"] += count
                        except Exception as e:
                            result["errors"].append(f"quiz generation error: {e}")
                        break

    # save output
    ensure_output_dir()
    output_file = OUTPUT_DIR / f"{discipline}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "discipline": discipline,
            "timestamp": datetime.now().isoformat(),
            "papers": [
                {
                    "doi": p["doi"],
                    "title": p["title"],
                    "curriculum_connection": p["connection"],
                    "html": p["html"],
                }
                for p in matched_papers
            ],
            "stats": result,
        }, f, indent=2)

    if verbose:
        print(f"\n=== RESULTS: {discipline.upper()} ===")
        print(f"  Papers fetched: {result['papers_fetched']}")
        print(f"  Papers matched: {result['papers_matched']}")
        print(f"  Quizzes generated: {result['quizzes_generated']}")
        if result['errors']:
            print(f"  Errors: {len(result['errors'])}")
        print(f"  Output: {output_file}")

    return result


def process_all_disciplines(generate_quizzes: bool = True):
    """process all disciplines"""

    print("\n=== CURRICULUM PIPELINE - ALL DISCIPLINES ===")

    total_results = {
        "papers_fetched": 0,
        "papers_matched": 0,
        "quizzes_generated": 0,
        "by_discipline": {},
    }

    for discipline in SOURCES.keys():
        result = process_discipline(discipline, generate_quizzes=generate_quizzes)
        total_results["papers_fetched"] += result["papers_fetched"]
        total_results["papers_matched"] += result["papers_matched"]
        total_results["quizzes_generated"] += result["quizzes_generated"]
        total_results["by_discipline"][discipline] = result

    print("\n=== PIPELINE COMPLETE ===")
    print(f"  Total papers fetched: {total_results['papers_fetched']}")
    print(f"  Total papers matched: {total_results['papers_matched']}")
    print(f"  Total quizzes generated: {total_results['quizzes_generated']}")


def main():
    parser = argparse.ArgumentParser(description="End-to-end curriculum pipeline")
    parser.add_argument("discipline", nargs="?", help="Discipline to process")
    parser.add_argument("--all", action="store_true", help="Process all disciplines")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--no-quizzes", action="store_true", help="Skip quiz generation")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.all:
        process_all_disciplines(generate_quizzes=not args.no_quizzes)
        return

    if args.discipline:
        if args.discipline not in SOURCES:
            print(f"[!] unknown discipline: {args.discipline}")
            print(f"    available: {', '.join(SOURCES.keys())}")
            return
        process_discipline(args.discipline, generate_quizzes=not args.no_quizzes)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
