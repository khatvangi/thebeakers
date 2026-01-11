#!/usr/bin/env python3
"""
run_daily_digest.py - orchestrates the daily digest pipeline

steps:
1. collect from OA feeds + secondary discovery
2. run triage on new articles
3. fetch fulltext for triaged articles
4. evidence upgrade for low-E articles with fulltext
5. select daily quota (blurbs + digests)
6. render digest page
7. send email campaign

run: python run_daily_digest.py
     python run_daily_digest.py --dry-run
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LOG_DIR = SCRIPT_DIR.parent / "logs"


def log(msg: str):
    """print with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run_step(name: str, cmd: list, dry_run: bool = False) -> bool:
    """run a pipeline step"""
    log(f"=== {name} ===")
    if dry_run:
        log(f"  [dry-run] would run: {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            log(f"  OK")
            # print last few lines of output
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:
                log(f"    {line}")
            return True
        else:
            log(f"  FAILED (exit {result.returncode})")
            log(f"    stderr: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT")
        return False
    except Exception as e:
        log(f"  ERROR: {e}")
        return False


def run_daily_digest(dry_run: bool = False, skip_email: bool = False):
    """run the full daily digest pipeline"""
    week = datetime.now().strftime("%Y-%m-%d")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log(f"=== DAILY DIGEST PIPELINE ===")
    log(f"date: {week}")
    log(f"dry_run: {dry_run}")

    # step 1: collect OA feeds
    run_step("1. COLLECT OA FEEDS", [
        sys.executable, str(SCRIPT_DIR / "feed_collector_oa.py"),
        "--limit", "100"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 2: secondary discovery
    run_step("2. SECONDARY DISCOVERY", [
        sys.executable, str(SCRIPT_DIR / "secondary_discovery.py"),
        "--limit", "50"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 3: triage new articles
    run_step("3. TRIAGE", [
        sys.executable, str(SCRIPT_DIR / "triage.py"),
        "--week", week,
        "--disciplines", "biology,chemistry,physics,ai,engineering,mathematics",
        "--limit", "30"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 4: fetch fulltext
    run_step("4. FULLTEXT FETCH", [
        sys.executable, str(SCRIPT_DIR / "stage0_fulltext_fetch.py"),
        "--limit", "20"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 5: evidence upgrade
    run_step("5. EVIDENCE UPGRADE", [
        sys.executable, str(SCRIPT_DIR / "triage_evidence_upgrade.py"),
        "--limit", "10"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 6: select daily issue
    run_step("6. SELECT DAILY ISSUE", [
        sys.executable, str(SCRIPT_DIR / "select_weekly_issue.py"),
        "--week", week,
        "--disciplines", "biology,chemistry,physics,ai,engineering,mathematics"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 7: render digest page (TODO: implement)
    log("=== 7. RENDER DIGEST ===")
    log("  [TODO] render_digest_page.py not yet implemented")

    # step 8: send email
    if not skip_email:
        log("=== 8. SEND EMAIL ===")
        log("  [TODO] send_campaign not yet implemented for daily")
    else:
        log("=== 8. SEND EMAIL (skipped) ===")

    log(f"\n=== PIPELINE COMPLETE ===")


def main():
    parser = argparse.ArgumentParser(description="run daily digest pipeline")
    parser.add_argument("--dry-run", action="store_true", help="don't make changes")
    parser.add_argument("--skip-email", action="store_true", help="skip email send")

    args = parser.parse_args()
    run_daily_digest(args.dry_run, args.skip_email)


if __name__ == "__main__":
    main()
