#!/usr/bin/env python3
"""
bootstrap_listmonk.py - create lists and store IDs for TheBeakers

creates:
- beakers_daily (daily/bi-daily digest subscribers)
- beakers_weekly (weekly deep dive subscribers)
- beakers_education (education highlight subscribers)

stores IDs in config/listmonk_ids.json
"""

import json
import os
import requests
from pathlib import Path

# config
LISTMONK_BASE_URL = os.environ.get("LISTMONK_BASE_URL", "http://localhost:9000")
LISTMONK_USER = os.environ.get("LISTMONK_USER", "admin")
LISTMONK_PASS = os.environ.get("LISTMONK_PASS", "spsdaily2026")

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
IDS_FILE = CONFIG_DIR / "listmonk_ids.json"

# lists to create
LISTS = [
    {
        "name": "beakers_daily",
        "type": "public",
        "optin": "double",
        "description": "Daily/bi-daily digest of research summaries"
    },
    {
        "name": "beakers_weekly",
        "type": "public",
        "optin": "double",
        "description": "Weekly deep dive articles with audio/video"
    },
    {
        "name": "beakers_education",
        "type": "public",
        "optin": "double",
        "description": "Weekly education highlights for instructors"
    }
]


def get_auth():
    return (LISTMONK_USER, LISTMONK_PASS)


def fetch_existing_lists():
    """fetch all existing lists"""
    resp = requests.get(
        f"{LISTMONK_BASE_URL}/api/lists",
        auth=get_auth(),
        timeout=10
    )
    resp.raise_for_status()
    return {lst["name"]: lst for lst in resp.json()["data"]["results"]}


def create_list(list_config):
    """create a single list"""
    resp = requests.post(
        f"{LISTMONK_BASE_URL}/api/lists",
        auth=get_auth(),
        json=list_config,
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()["data"]


def bootstrap_lists():
    """create lists if they don't exist, return ID mapping"""
    existing = fetch_existing_lists()
    ids = {}

    for lst in LISTS:
        name = lst["name"]
        if name in existing:
            print(f"  [exists] {name} (id={existing[name]['id']})")
            ids[name] = existing[name]["id"]
        else:
            print(f"  [create] {name}...")
            created = create_list(lst)
            ids[name] = created["id"]
            print(f"           created with id={created['id']}")

    return ids


def save_ids(ids):
    """save list IDs to config file"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    IDS_FILE.write_text(json.dumps(ids, indent=2))
    print(f"\nsaved to {IDS_FILE}")


def load_ids():
    """load list IDs from config file"""
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text())
    return None


def main():
    print("=== LISTMONK BOOTSTRAP ===")
    print(f"base URL: {LISTMONK_BASE_URL}")

    # check connection
    try:
        resp = requests.get(f"{LISTMONK_BASE_URL}/api/health", timeout=5)
        print(f"health: {resp.status_code}")
    except Exception as e:
        print(f"error: cannot reach listmonk at {LISTMONK_BASE_URL}")
        print(f"       {e}")
        return 1

    # bootstrap
    try:
        ids = bootstrap_lists()
        save_ids(ids)
        print("\n=== DONE ===")
        for name, list_id in ids.items():
            print(f"  {name}: {list_id}")
        return 0
    except Exception as e:
        print(f"error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
