#!/usr/bin/env python3
"""
db_schema_triage.py - add triage tables to articles.db

idempotent: safe to run multiple times
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"


def ensure_triage_schema(conn: sqlite3.Connection) -> None:
    """create triage tables if they don't exist"""

    cursor = conn.cursor()

    # triage_run: tracks each triage batch
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triage_run (
            run_id TEXT PRIMARY KEY,
            week_of TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            model_builder TEXT,
            model_skeptic TEXT,
            config_json TEXT
        )
    """)

    # model_vote: raw outputs from each model (for audit)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_vote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            article_url TEXT NOT NULL,
            role TEXT NOT NULL,
            model_name TEXT NOT NULL,
            prompt_hash TEXT,
            json_output TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES triage_run(run_id)
        )
    """)

    # triage_result: final routing decision per article
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triage_result (
            run_id TEXT NOT NULL,
            article_url TEXT NOT NULL,
            discipline TEXT,

            -- S,E,T,M,H scores (0-5)
            score_s INTEGER,  -- scientific significance
            score_e INTEGER,  -- evidence strength
            score_t INTEGER,  -- teachability
            score_m INTEGER,  -- media affordance
            score_h INTEGER,  -- hype risk (penalty)

            -- routing
            route TEXT,  -- indepth | digest | blurb | reject
            frontier_flag INTEGER DEFAULT 0,
            difficulty TEXT,  -- easy | medium | hard

            -- metadata
            tldr TEXT,
            pivot_figure_prompt TEXT,
            course_hooks_json TEXT,
            skill_hooks_json TEXT,

            -- fulltext tracking
            fulltext_path TEXT,
            fulltext_ok INTEGER DEFAULT 0,
            fulltext_source TEXT,  -- unpaywall | pmc | arxiv_direct | manual
            fulltext_fetched_at TEXT,

            -- access state (for routing decisions)
            access_state TEXT DEFAULT 'unknown',  -- unknown | abstract_only | oa_pdf_found | paywalled

            -- status
            status TEXT DEFAULT 'ok',  -- ok | error
            error_msg TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_id, article_url)
        )
    """)

    # add columns if table exists but columns don't (migration)
    try:
        cursor.execute("ALTER TABLE triage_result ADD COLUMN fulltext_path TEXT")
    except sqlite3.OperationalError:
        pass  # column exists
    try:
        cursor.execute("ALTER TABLE triage_result ADD COLUMN fulltext_ok INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE triage_result ADD COLUMN fulltext_source TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE triage_result ADD COLUMN fulltext_fetched_at TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE triage_result ADD COLUMN access_state TEXT DEFAULT 'unknown'")
    except sqlite3.OperationalError:
        pass

    # truth_ledger_claim: claims from triage (simpler than full Stage 1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS truth_ledger_claim (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            article_url TEXT NOT NULL,
            claim_id TEXT,
            claim_text TEXT,
            verdict TEXT,  -- keep | uncertain | reject
            support_roles_json TEXT,
            anchors_json TEXT,
            confounds_json TEXT,
            confidence REAL,
            falsify_test TEXT,
            FOREIGN KEY (run_id) REFERENCES triage_run(run_id)
        )
    """)

    # note_stub: pre-generated content stubs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS note_stub (
            note_id TEXT PRIMARY KEY,
            article_url TEXT NOT NULL,
            type TEXT,  -- indepth | digest | blurb
            discipline TEXT,
            week_of TEXT,
            slug TEXT,
            title TEXT,
            json_body TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    print("triage schema ensured")


def main():
    if not DB_PATH.exists():
        print(f"error: database not found at {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    ensure_triage_schema(conn)
    conn.close()

    print(f"triage tables added to {DB_PATH}")
    return 0


if __name__ == "__main__":
    exit(main())
