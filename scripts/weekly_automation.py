#!/usr/bin/env python3
"""
weekly_automation.py - Weekly pipeline + archive + deploy

Runs every Monday:
1. Collect articles from all sources
2. Run weekly pipeline (triage, generate, etc.)
3. Archive old content (>30 days)
4. Generate indexes
5. Git commit & push (auto-deploy to Cloudflare Pages)

Usage:
    python weekly_automation.py           # full run
    python weekly_automation.py --dry-run # preview only
    python weekly_automation.py --step collect  # run single step
"""

import argparse
import subprocess
import sqlite3
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path

# paths
ROOT = Path("/storage/thebeakers")
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
ARCHIVE = DATA / "archive"
LOGS = ROOT / "logs"
DB_PATH = DATA / "articles.db"

# subjects
SUBJECTS = ["chemistry", "physics", "biology", "mathematics", "engineering", "ai", "agriculture"]


def log(msg: str, level: str = "INFO"):
    """log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def run_cmd(cmd: list, description: str, dry_run: bool = False, timeout: int = 600) -> bool:
    """run a shell command"""
    log(f"Running: {description}")

    if dry_run:
        log(f"  [dry-run] {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT)
        )
        if result.returncode == 0:
            log(f"  ✓ {description} completed")
            # show last 3 lines of output
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[-3:]:
                    log(f"    {line}")
            return True
        else:
            log(f"  ✗ {description} failed (exit {result.returncode})", "ERROR")
            if result.stderr:
                log(f"    {result.stderr[:200]}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log(f"  ✗ {description} timed out", "ERROR")
        return False
    except Exception as e:
        log(f"  ✗ {description} error: {e}", "ERROR")
        return False


def step_collect(dry_run: bool = False) -> bool:
    """collect articles from all feeds"""
    log("=" * 50)
    log("STEP 1: Collect Articles")
    log("=" * 50)

    # society fetcher for each discipline
    for subject in SUBJECTS:
        run_cmd(
            ["python", str(SCRIPTS / "society_fetcher.py"), subject],
            f"Fetch {subject} papers",
            dry_run
        )

    # feed collector
    run_cmd(
        ["python", str(SCRIPTS / "feed_collector.py")],
        "Collect from RSS feeds",
        dry_run
    )

    return True


def step_pipeline(dry_run: bool = False) -> bool:
    """run weekly pipeline"""
    log("=" * 50)
    log("STEP 2: Weekly Pipeline")
    log("=" * 50)

    # weekly pipeline handles triage, scoring, generation
    return run_cmd(
        ["python", str(SCRIPTS / "weekly_pipeline.py")],
        "Run weekly pipeline",
        dry_run,
        timeout=1800  # 30 min for full pipeline
    )


def step_archive(dry_run: bool = False, days: int = 30) -> bool:
    """archive old articles and digests"""
    log("=" * 50)
    log(f"STEP 3: Archive Content (>{days} days old)")
    log("=" * 50)

    ARCHIVE.mkdir(exist_ok=True)
    cutoff = datetime.now() - timedelta(days=days)
    archived_count = 0

    # archive old digest files
    digest_dir = DATA
    for f in digest_dir.glob("digest_*.html"):
        try:
            # parse date from filename: digest_2026-01-15.html
            date_str = f.stem.replace("digest_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff:
                dest = ARCHIVE / f.name
                if dry_run:
                    log(f"  [dry-run] Would archive: {f.name}")
                else:
                    shutil.move(str(f), str(dest))
                    log(f"  Archived: {f.name}")
                archived_count += 1
        except ValueError:
            continue  # skip files with unexpected names

    # clean up old entries in database
    if not dry_run and DB_PATH.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # mark old seen_articles as archived
            cutoff_str = cutoff.strftime("%Y-%m-%d")
            cursor.execute("""
                UPDATE seen_articles
                SET status = 'archived'
                WHERE collected_at < ? AND status = 'pending'
            """, (cutoff_str,))

            db_archived = cursor.rowcount
            conn.commit()
            conn.close()

            if db_archived > 0:
                log(f"  Marked {db_archived} old DB entries as archived")
        except Exception as e:
            log(f"  DB archive warning: {e}", "WARN")

    log(f"  Total files archived: {archived_count}")
    return True


def step_indexes(dry_run: bool = False) -> bool:
    """regenerate article indexes"""
    log("=" * 50)
    log("STEP 4: Generate Indexes")
    log("=" * 50)

    return run_cmd(
        ["python", str(SCRIPTS / "generate_indexes.py")],
        "Generate article indexes",
        dry_run
    )


def step_deploy(dry_run: bool = False) -> bool:
    """commit and push to deploy"""
    log("=" * 50)
    log("STEP 5: Deploy to Cloudflare Pages")
    log("=" * 50)

    # check if there are changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=str(ROOT)
    )

    if not result.stdout.strip():
        log("  No changes to deploy")
        return True

    # get summary of changes
    changes = result.stdout.strip().split('\n')
    log(f"  {len(changes)} files changed")

    if dry_run:
        log("  [dry-run] Would commit and push")
        for c in changes[:5]:
            log(f"    {c}")
        if len(changes) > 5:
            log(f"    ... and {len(changes) - 5} more")
        return True

    # stage all changes (excluding large files and node_modules)
    run_cmd(
        ["git", "add", "-A"],
        "Stage changes",
        dry_run
    )

    # commit
    date_str = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"Weekly update {date_str}\n\n- Auto-generated by weekly_automation.py"

    run_cmd(
        ["git", "commit", "-m", commit_msg],
        "Commit changes",
        dry_run
    )

    # push
    success = run_cmd(
        ["git", "push"],
        "Push to GitHub",
        dry_run
    )

    if success:
        log("  ✓ Deployed! Cloudflare Pages will auto-build.")

    return success


def main():
    parser = argparse.ArgumentParser(description="Weekly automation for The Beakers")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--step", choices=["collect", "pipeline", "archive", "indexes", "deploy"],
                        help="Run single step only")
    parser.add_argument("--archive-days", type=int, default=30, help="Archive content older than N days")
    args = parser.parse_args()

    # setup logging
    LOGS.mkdir(exist_ok=True)
    log_file = LOGS / f"weekly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    log("=" * 60)
    log("THE BEAKERS - WEEKLY AUTOMATION")
    log(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    log("=" * 60)

    steps = {
        "collect": lambda: step_collect(args.dry_run),
        "pipeline": lambda: step_pipeline(args.dry_run),
        "archive": lambda: step_archive(args.dry_run, args.archive_days),
        "indexes": lambda: step_indexes(args.dry_run),
        "deploy": lambda: step_deploy(args.dry_run),
    }

    if args.step:
        # run single step
        success = steps[args.step]()
    else:
        # run all steps
        success = True
        for name, func in steps.items():
            if not func():
                log(f"Step {name} failed, continuing...", "WARN")
                success = False

    log("=" * 60)
    log(f"COMPLETED {'(with warnings)' if not success else 'successfully'}")
    log("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
