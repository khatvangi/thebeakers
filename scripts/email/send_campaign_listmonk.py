#!/usr/bin/env python3
"""
send_campaign_listmonk.py - create and send listmonk campaigns

usage:
  python send_campaign_listmonk.py --cadence daily --html path/to/issue.html --subject "TheBeakers — Daily Digest"
  python send_campaign_listmonk.py --cadence weekly --html path/to/deepdive.html --subject "TheBeakers — Weekly Deep Dives"

creates campaign in listmonk, targets appropriate list(s), and sends
"""

import argparse
import json
import os
import requests
from datetime import datetime
from pathlib import Path

# config
LISTMONK_BASE_URL = os.environ.get("LISTMONK_BASE_URL", "http://localhost:9000")
LISTMONK_USER = os.environ.get("LISTMONK_USER", "admin")
LISTMONK_PASS = os.environ.get("LISTMONK_PASS", "spsdaily2026")

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
IDS_FILE = CONFIG_DIR / "listmonk_ids.json"

# cadence to list mapping
CADENCE_MAP = {
    "daily": "beakers_daily",
    "bi_daily": "beakers_daily",
    "weekly": "beakers_weekly",
    "education": "beakers_education",
}


def get_auth():
    return (LISTMONK_USER, LISTMONK_PASS)


def load_list_ids():
    """load list IDs from config"""
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text())
    return {
        "beakers_daily": 4,
        "beakers_weekly": 5,
        "beakers_education": 6
    }


def load_html(filepath: str) -> str:
    """load HTML content from file"""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def create_campaign(
    name: str,
    subject: str,
    body: str,
    list_ids: list,
    from_email: str = "TheBeakers <thebeakerscom@gmail.com>",
    content_type: str = "html"
) -> dict:
    """create a new campaign in listmonk"""
    payload = {
        "name": name,
        "subject": subject,
        "lists": list_ids,
        "from_email": from_email,
        "type": "regular",
        "content_type": content_type,
        "body": body,
        "tags": ["automated"],
    }

    resp = requests.post(
        f"{LISTMONK_BASE_URL}/api/campaigns",
        auth=get_auth(),
        json=payload,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["data"]


def start_campaign(campaign_id: int) -> dict:
    """start/send a campaign"""
    resp = requests.put(
        f"{LISTMONK_BASE_URL}/api/campaigns/{campaign_id}/status",
        auth=get_auth(),
        json={"status": "running"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["data"]


def send_campaign(
    cadence: str,
    html_path: str,
    subject: str,
    send_now: bool = True,
    dry_run: bool = False
) -> dict:
    """create and optionally send a campaign"""
    list_ids_config = load_list_ids()

    # map cadence to list
    list_name = CADENCE_MAP.get(cadence, "beakers_daily")
    list_id = list_ids_config.get(list_name)

    if not list_id:
        raise ValueError(f"no list ID for {list_name}")

    # load HTML
    body = load_html(html_path)

    # generate campaign name
    date_str = datetime.now().strftime("%Y-%m-%d")
    name = f"{cadence.capitalize()} Issue - {date_str}"

    print(f"=== CREATE CAMPAIGN ===")
    print(f"name: {name}")
    print(f"subject: {subject}")
    print(f"list: {list_name} (id={list_id})")
    print(f"html: {html_path} ({len(body)} chars)")

    if dry_run:
        print("[dry-run] would create and send campaign")
        return {"dry_run": True, "name": name}

    # create campaign
    campaign = create_campaign(
        name=name,
        subject=subject,
        body=body,
        list_ids=[list_id]
    )
    campaign_id = campaign["id"]
    print(f"created campaign id={campaign_id}")

    # optionally send
    if send_now:
        result = start_campaign(campaign_id)
        print(f"campaign started: status={result.get('status')}")
        return {"campaign_id": campaign_id, "status": "running"}
    else:
        print(f"campaign created but not sent (use --send to send)")
        return {"campaign_id": campaign_id, "status": "draft"}


def main():
    parser = argparse.ArgumentParser(description="send listmonk campaign")
    parser.add_argument("--cadence", required=True, choices=["daily", "bi_daily", "weekly", "education"],
                        help="campaign cadence (determines target list)")
    parser.add_argument("--html", required=True, help="path to HTML file")
    parser.add_argument("--subject", required=True, help="email subject line")
    parser.add_argument("--send", action="store_true", help="actually send (default: create draft)")
    parser.add_argument("--dry-run", action="store_true", help="don't create campaign")

    args = parser.parse_args()

    send_campaign(
        cadence=args.cadence,
        html_path=args.html,
        subject=args.subject,
        send_now=args.send,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
