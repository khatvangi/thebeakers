#!/usr/bin/env python3
"""
backfill_abstracts.py - fetch missing abstracts from OpenAlex

updates society_papers database with abstracts for papers that don't have them.

usage:
    python scripts/backfill_abstracts.py           # backfill all
    python scripts/backfill_abstracts.py chemistry # backfill one discipline
    python scripts/backfill_abstracts.py --dry-run # check without updating
"""

import argparse
import sqlite3
import requests
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
HEADERS = {"User-Agent": "TheBeakers/1.0 (mailto:thebeakerscom@gmail.com)"}


def reconstruct_abstract(inverted_index: dict) -> str:
    """reconstruct abstract from OpenAlex inverted index format"""
    if not inverted_index:
        return ""
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words.keys()))


def fetch_abstract_from_openalex(doi: str) -> str:
    """fetch abstract from OpenAlex API"""
    try:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            inverted = data.get("abstract_inverted_index")
            if inverted:
                return reconstruct_abstract(inverted)
    except Exception as e:
        print(f"  [!] error: {e}")
    return ""


def backfill(discipline: str = None, dry_run: bool = False):
    """backfill missing abstracts"""

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # get papers without abstracts
    if discipline:
        cur.execute("""
            SELECT doi, title FROM society_papers
            WHERE discipline = ? AND (abstract IS NULL OR abstract = '')
        """, (discipline,))
    else:
        cur.execute("""
            SELECT doi, title FROM society_papers
            WHERE abstract IS NULL OR abstract = ''
        """)

    papers = cur.fetchall()
    print(f"Found {len(papers)} papers without abstracts\n")

    updated = 0
    for doi, title in papers:
        print(f"[{doi}] {title[:50]}...")

        abstract = fetch_abstract_from_openalex(doi)

        if abstract:
            print(f"  found abstract ({len(abstract)} chars)")
            if not dry_run:
                cur.execute("""
                    UPDATE society_papers SET abstract = ? WHERE doi = ?
                """, (abstract, doi))
                conn.commit()
            updated += 1
        else:
            print(f"  no abstract available")

        time.sleep(0.5)  # rate limit

    conn.close()

    action = "would update" if dry_run else "updated"
    print(f"\n=== {action.upper()} {updated} of {len(papers)} papers ===")


def main():
    parser = argparse.ArgumentParser(description="Backfill missing abstracts from OpenAlex")
    parser.add_argument("discipline", nargs="?", help="Discipline to backfill")
    parser.add_argument("--dry-run", action="store_true", help="Check without updating")
    args = parser.parse_args()

    backfill(args.discipline, args.dry_run)


if __name__ == "__main__":
    main()
