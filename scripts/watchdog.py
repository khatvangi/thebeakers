#!/usr/bin/env python3
"""
watchdog.py - monitor both daily and weekly pipelines + content freshness

designed to run via systemd timer every 12 hours.
alerts via telegram if either pipeline hasn't reported success within its
expected window, OR if user-facing content stops changing (silent staleness).
"""

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOGS = ROOT / "logs"

# (label, health_file, max_age_hours) — daily expects within 26h, weekly within 8 days
PIPELINES = [
    ("daily",  LOGS / "daily-digest-health.json",   26),
    ("weekly", LOGS / "weekly-deepdive-health.json", 24 * 8),
    ("weekly-auto", LOGS / "weekly-automation-health.json", 24 * 8),
]

# files whose content should change at least every N hours. catches the
# "pipeline OK but produced identical output" class of bug — the failure
# mode where every step exits 0 yet the homepage looks frozen.
# see pipeline_failures.md "Silent staleness".
CONTENT_FRESHNESS = [
    (ROOT / "data" / "latest.json", 30),
]
CONTENT_HASH_STORE = LOGS / "content-hashes.json"

# telegram (Beakers STEM Curator bot) — secrets loaded from gitignored scripts/_secrets.py
try:
    from _secrets import BOT_TOKEN, CHAT_ID
except ImportError:
    BOT_TOKEN = os.environ.get("BEAKERS_BOT_TOKEN", "")
    CHAT_ID = os.environ.get("BEAKERS_CHAT_ID", "")


def send_telegram(msg):
    try:
        data = json.dumps({"chat_id": CHAT_ID, "text": msg}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"telegram failed: {e}")


def check_pipeline(label, health_file, max_age_hours):
    now = datetime.now()

    if not health_file.exists():
        send_telegram(f"Beakers watchdog [{label}]: no health file. Pipeline may have never run successfully.")
        return

    health = json.loads(health_file.read_text())
    ts = datetime.fromisoformat(health["timestamp"])
    age = now - ts
    status = health.get("status", "unknown")
    age_h = age.total_seconds() / 3600

    if age > timedelta(hours=max_age_hours):
        send_telegram(
            f"Beakers watchdog [{label}]: last run {age_h:.1f}h ago "
            f"(status: {status}). Expected within {max_age_hours}h."
        )
    elif status == "failed":
        send_telegram(
            f"Beakers watchdog [{label}]: last run FAILED at {ts.strftime('%H:%M %Y-%m-%d')}. "
            f"Details: {health.get('details', 'none')}"
        )
    else:
        print(f"ok [{label}]: last run {age_h:.1f}h ago, status={status}")


def check_content_freshness():
    """alert if a file's content hash hasn't changed within its allowed window.

    persists {path: {sha, last_changed_at}} in CONTENT_HASH_STORE. on each
    run we hash the file, compare to stored. if hash differs, record the
    change. if identical AND past the threshold since last change, alert.
    """
    now = datetime.now()
    store = {}
    if CONTENT_HASH_STORE.exists():
        try:
            store = json.loads(CONTENT_HASH_STORE.read_text())
        except Exception:
            store = {}

    for path, max_unchanged_h in CONTENT_FRESHNESS:
        key = str(path)
        if not path.exists():
            send_telegram(f"Beakers watchdog [content]: {path.name} missing")
            continue

        current_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        prev = store.get(key, {})

        if prev.get("sha") != current_sha:
            store[key] = {"sha": current_sha, "last_changed_at": now.isoformat()}
            print(f"ok [content]: {path.name} changed since last check")
            continue

        # hash unchanged — how long has it been frozen?
        last_changed = prev.get("last_changed_at")
        if last_changed:
            age_h = (now - datetime.fromisoformat(last_changed)).total_seconds() / 3600
            if age_h > max_unchanged_h:
                send_telegram(
                    f"Beakers watchdog [content]: {path.name} unchanged for "
                    f"{age_h:.1f}h (threshold {max_unchanged_h}h). Pipeline may "
                    f"be running but producing identical output."
                )
            else:
                print(f"ok [content]: {path.name} unchanged for {age_h:.1f}h "
                      f"(under {max_unchanged_h}h threshold)")

    CONTENT_HASH_STORE.write_text(json.dumps(store, indent=2))


if __name__ == "__main__":
    for label, health_file, max_age in PIPELINES:
        check_pipeline(label, health_file, max_age)
    check_content_freshness()
