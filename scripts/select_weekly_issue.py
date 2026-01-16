#!/usr/bin/env python3
"""
select_weekly_issue.py - deterministic weekly quotas per discipline

quotas per {week_of, discipline}:
- 1 indepth (requires oa_pdf_found)
- 3-7 digest (requires oa_pdf_found)
- 10-30 blurbs (allows abstract_only, labeled "Frontier")

ranking formula: 0.55*E + 0.45*T - 0.60*H + 0.25*S + 0.15*M
"""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"

# quotas per discipline per week
QUOTAS = {
    "indepth": 1,
    "digest_min": 3,
    "digest_max": 7,
    "blurb_min": 10,
    "blurb_max": 30,
}


def ensure_issue_schema(conn: sqlite3.Connection) -> None:
    """create issue table if not exists"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS issue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_of TEXT NOT NULL,
            discipline TEXT NOT NULL,
            article_url TEXT NOT NULL,
            slot TEXT NOT NULL,  -- indepth | digest | blurb
            rank_score REAL,
            access_state TEXT,
            selected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(week_of, discipline, article_url)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_issue_week ON issue(week_of, discipline)
    """)
    conn.commit()


def compute_rank_score(row: sqlite3.Row) -> float:
    """compute ranking score: 0.55*E + 0.45*T - 0.60*H + 0.25*S + 0.15*M"""
    S = row["score_s"] or 0
    E = row["score_e"] or 0
    T = row["score_t"] or 0
    M = row["score_m"] or 0
    H = row["score_h"] or 0
    return 0.55 * E + 0.45 * T - 0.60 * H + 0.25 * S + 0.15 * M


def select_for_discipline(
    conn: sqlite3.Connection,
    week_of: str,
    discipline: str,
    dry_run: bool = False
) -> Dict:
    """select articles for one discipline's weekly issue"""

    # check if already selected
    existing = conn.execute("""
        SELECT COUNT(*) FROM issue WHERE week_of = ? AND discipline = ?
    """, (week_of, discipline)).fetchone()[0]

    if existing > 0:
        print(f"  [{discipline}] already has {existing} articles selected for {week_of}")
        return {"indepth": 0, "digest": 0, "blurb": 0, "skipped": True}

    results = {"indepth": 0, "digest": 0, "blurb": 0}

    # 1. Select indepth (requires oa_pdf_found, route='indepth')
    cursor = conn.execute("""
        SELECT article_url, score_s, score_e, score_t, score_m, score_h, access_state
        FROM triage_result
        WHERE discipline = ?
          AND route = 'indepth'
          AND access_state = 'oa_pdf_found'
          AND status = 'ok'
        ORDER BY score_e DESC, score_t DESC
        LIMIT ?
    """, (discipline, QUOTAS["indepth"]))

    for row in cursor.fetchall():
        score = compute_rank_score(row)
        if not dry_run:
            conn.execute("""
                INSERT OR IGNORE INTO issue (week_of, discipline, article_url, slot, rank_score, access_state)
                VALUES (?, ?, ?, 'indepth', ?, ?)
            """, (week_of, discipline, row["article_url"], score, row["access_state"]))
        results["indepth"] += 1
        print(f"    [indepth] {row['article_url'][:50]}... (score={score:.2f})")

    # 2. Select digest (requires oa_pdf_found, route='digest')
    cursor = conn.execute("""
        SELECT article_url, score_s, score_e, score_t, score_m, score_h, access_state
        FROM triage_result
        WHERE discipline = ?
          AND route = 'digest'
          AND access_state = 'oa_pdf_found'
          AND status = 'ok'
        ORDER BY score_e DESC, score_t DESC
        LIMIT ?
    """, (discipline, QUOTAS["digest_max"]))

    for row in cursor.fetchall():
        score = compute_rank_score(row)
        if not dry_run:
            conn.execute("""
                INSERT OR IGNORE INTO issue (week_of, discipline, article_url, slot, rank_score, access_state)
                VALUES (?, ?, ?, 'digest', ?, ?)
            """, (week_of, discipline, row["article_url"], score, row["access_state"]))
        results["digest"] += 1
        print(f"    [digest] {row['article_url'][:50]}... (score={score:.2f})")

    # 3. Select blurbs (allows abstract_only, route='blurb')
    # first try oa_pdf_found, then abstract_only
    cursor = conn.execute("""
        SELECT article_url, score_s, score_e, score_t, score_m, score_h, access_state
        FROM triage_result
        WHERE discipline = ?
          AND route = 'blurb'
          AND access_state IN ('oa_pdf_found', 'abstract_only')
          AND status = 'ok'
        ORDER BY
            CASE access_state WHEN 'oa_pdf_found' THEN 0 ELSE 1 END,
            score_s DESC, score_t DESC
        LIMIT ?
    """, (discipline, QUOTAS["blurb_max"]))

    for row in cursor.fetchall():
        score = compute_rank_score(row)
        label = "" if row["access_state"] == "oa_pdf_found" else " (Frontier)"
        if not dry_run:
            conn.execute("""
                INSERT OR IGNORE INTO issue (week_of, discipline, article_url, slot, rank_score, access_state)
                VALUES (?, ?, ?, 'blurb', ?, ?)
            """, (week_of, discipline, row["article_url"], score, row["access_state"]))
        results["blurb"] += 1
        print(f"    [blurb{label}] {row['article_url'][:50]}... (score={score:.2f})")

    if not dry_run:
        conn.commit()

    return results


def select_weekly_issue(
    week_of: str,
    disciplines: List[str],
    dry_run: bool = False
) -> Dict:
    """select articles for all disciplines"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_issue_schema(conn)

    print(f"=== WEEKLY ISSUE SELECTION ===")
    print(f"week: {week_of}")
    print(f"disciplines: {disciplines}")

    totals = {"indepth": 0, "digest": 0, "blurb": 0}

    for discipline in disciplines:
        print(f"\n>>> {discipline}")
        results = select_for_discipline(conn, week_of, discipline, dry_run)
        if not results.get("skipped"):
            totals["indepth"] += results["indepth"]
            totals["digest"] += results["digest"]
            totals["blurb"] += results["blurb"]

    conn.close()

    print(f"\n=== SUMMARY ===")
    print(f"indepth: {totals['indepth']}")
    print(f"digest: {totals['digest']}")
    print(f"blurb: {totals['blurb']}")

    return totals


def get_issue_articles(week_of: str, discipline: str = None, slot: str = None) -> List[Dict]:
    """retrieve selected articles for an issue"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM issue WHERE week_of = ?"
    params = [week_of]

    if discipline:
        query += " AND discipline = ?"
        params.append(discipline)
    if slot:
        query += " AND slot = ?"
        params.append(slot)

    query += " ORDER BY discipline, slot, rank_score DESC"

    cursor = conn.execute(query, params)
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return articles


def main():
    parser = argparse.ArgumentParser(description="select articles for weekly issue")
    parser.add_argument("--week", default=datetime.now().strftime("%Y-%m-%d"),
                        help="week to select for (YYYY-MM-DD)")
    parser.add_argument("--disciplines", default="biology,chemistry,physics,ai,engineering,mathematics",
                        help="comma-separated disciplines")
    parser.add_argument("--dry-run", action="store_true", help="don't save selections")
    parser.add_argument("--show", action="store_true", help="show current selections")

    args = parser.parse_args()
    disciplines = [d.strip() for d in args.disciplines.split(",")]

    if args.show:
        articles = get_issue_articles(args.week)
        print(f"Issue {args.week}: {len(articles)} articles")
        for a in articles:
            print(f"  [{a['discipline']}:{a['slot']}] {a['article_url'][:50]}...")
    else:
        select_weekly_issue(args.week, disciplines, args.dry_run)


if __name__ == "__main__":
    main()
