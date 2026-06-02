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
import fcntl
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LOG_DIR = SCRIPT_DIR.parent / "logs"
LOCK_FILE = LOG_DIR / "daily-digest.lock"
HEALTH_FILE = LOG_DIR / "daily-digest-health.json"

# telegram alerts — secrets loaded from gitignored scripts/_secrets.py,
# falling back to env vars so systemd units can override without a checkout edit
try:
    from _secrets import BOT_TOKEN, CHAT_ID
except ImportError:
    BOT_TOKEN = os.environ.get("BEAKERS_BOT_TOKEN", "")
    CHAT_ID = os.environ.get("BEAKERS_CHAT_ID", "")


def log(msg: str):
    """print with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def send_telegram(msg: str):
    """send a telegram alert"""
    try:
        data = json.dumps({"chat_id": CHAT_ID, "text": msg}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log(f"  telegram alert failed: {e}")


def write_health(status: str, details: str = ""):
    """write health status file for watchdog"""
    HEALTH_FILE.write_text(json.dumps({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details,
    }))


# tracks which steps failed during the current run so the final health
# write reflects overall status. without this, a later successful step
# would overwrite the "failed" health written by an earlier broken step,
# blinding the watchdog. see pipeline_failures.md "Step 3 silent failure".
FAILED_STEPS: list = []


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
            # full stderr to log so a future debugger sees the whole trace,
            # truncated only for the telegram alert (Telegram cap ~4096 chars)
            log(f"    stderr: {result.stderr}")
            send_telegram(f"🧪 Beakers daily FAILED at step: {name}\n{result.stderr[:1500]}")
            FAILED_STEPS.append(name)
            return False
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT")
        send_telegram(f"🧪 Beakers daily TIMEOUT at step: {name}")
        FAILED_STEPS.append(f"{name} (timeout)")
        return False
    except Exception as e:
        log(f"  ERROR: {e}")
        send_telegram(f"🧪 Beakers daily ERROR at step: {name}\n{e}")
        FAILED_STEPS.append(f"{name} (error: {e})")
        return False


def run_daily_digest(dry_run: bool = False, skip_email: bool = False):
    """run the full daily digest pipeline"""
    week = datetime.now().strftime("%Y-%m-%d")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # flock-based locking (crash-safe — OS releases lock when process dies)
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("another instance is already running (flock held), exiting")
        return

    write_health("running", f"started {week}")

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
        "--disciplines", "biology,chemistry,physics,ai,engineering,mathematics,agriculture",
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
        "--disciplines", "biology,chemistry,physics,ai,engineering,mathematics,agriculture"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 7: render digest page
    output_file = SCRIPT_DIR.parent / "data" / f"digest_{week}.html"
    run_step("7. RENDER DIGEST", [
        sys.executable, str(SCRIPT_DIR / "render_digest_page.py"),
        "--week", week,
        "--output", str(output_file),
        "--title", f"The Beakers — Daily Digest ({week})"
    ] + (["--dry-run"] if dry_run else []), dry_run)

    # step 7b: update homepage headlines json
    run_step("7b. UPDATE HOMEPAGE JSON", [
        sys.executable, str(SCRIPT_DIR / "generate_latest_json.py"), week
    ], dry_run)

    # step 7c: refresh discipline pages with latest articles
    run_step("7c. REFRESH DISCIPLINE PAGES", [
        sys.executable, str(SCRIPT_DIR / "populate_discipline_pages.py")
    ], dry_run)

    # step 8: send email (--send actually triggers delivery, not just create draft)
    if not skip_email:
        run_step("8. SEND EMAIL", [
            sys.executable, str(SCRIPT_DIR / "email" / "send_campaign_listmonk.py"),
            "--cadence", "daily",
            "--html", str(output_file),
            "--subject", f"The Beakers — Daily Digest ({week})",
            "--send"
        ] + (["--dry-run"] if dry_run else []), dry_run)
    else:
        log("=== 8. SEND EMAIL (skipped) ===")

    # final health status reflects whether ANY step failed during this run.
    # watchdog reads this — never claim "ok" when something broke mid-pipeline.
    if FAILED_STEPS:
        details = f"{week} — failed steps: {', '.join(FAILED_STEPS)}"
        write_health("failed", details)
        log(f"\n=== PIPELINE COMPLETE WITH FAILURES ===")
        log(f"  failed steps: {FAILED_STEPS}")
    else:
        write_health("ok", f"completed {week}")
        log(f"\n=== PIPELINE COMPLETE ===")


def main():
    parser = argparse.ArgumentParser(description="run daily digest pipeline")
    parser.add_argument("--dry-run", action="store_true", help="don't make changes")
    parser.add_argument("--skip-email", action="store_true", help="skip email send")

    args = parser.parse_args()
    run_daily_digest(args.dry_run, args.skip_email)


if __name__ == "__main__":
    main()
