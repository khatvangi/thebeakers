#!/usr/bin/env python3
"""
subscribe_api.py - Flask API for TheBeakers subscriptions

endpoints:
- POST /api/subscribe - add/update subscriber in listmonk

run: gunicorn -w 2 -b 127.0.0.1:5050 subscribe_api:app
"""

import json
import os
import re
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

# config
LISTMONK_BASE_URL = os.environ.get("LISTMONK_BASE_URL", "http://localhost:9000")
LISTMONK_USER = os.environ.get("LISTMONK_USER", "admin")
LISTMONK_PASS = os.environ.get("LISTMONK_PASS", "spsdaily2026")

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
IDS_FILE = CONFIG_DIR / "listmonk_ids.json"

# valid values
VALID_CADENCES = {"daily", "bi_daily", "weekly"}
VALID_SUBJECTS = {"chemistry", "physics", "math", "engineering", "tech_cs", "biology", "agriculture"}

app = Flask(__name__)


def load_list_ids():
    """load list IDs from config"""
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text())
    # fallback to defaults
    return {
        "beakers_daily": 4,
        "beakers_weekly": 5,
        "beakers_education": 6
    }


def get_auth():
    return (LISTMONK_USER, LISTMONK_PASS)


def validate_email(email):
    """basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def cadence_to_list_ids(cadence, list_ids):
    """map cadence to list IDs"""
    if cadence == "daily" or cadence == "bi_daily":
        return [list_ids["beakers_daily"]]
    elif cadence == "weekly":
        return [list_ids["beakers_weekly"]]
    else:
        return [list_ids["beakers_daily"]]  # default


def upsert_subscriber(email, name, cadence, subjects, list_ids):
    """add or update subscriber in listmonk"""
    target_lists = cadence_to_list_ids(cadence, list_ids)

    # subscriber attributes
    attribs = {
        "cadence": cadence,
        "subjects": subjects,
        "source": "thebeakers.com",
        "subscribed_at": datetime.now().isoformat()
    }

    # try to create new subscriber first
    resp = requests.post(
        f"{LISTMONK_BASE_URL}/api/subscribers",
        auth=get_auth(),
        json={
            "email": email,
            "name": name or "",
            "attribs": attribs,
            "lists": target_lists,
            "status": "enabled"
        },
        timeout=10
    )

    if resp.status_code == 200:
        return {"action": "created", "id": resp.json()["data"]["id"]}
    elif resp.status_code == 409:
        # subscriber exists - get their ID and update
        # search through all subscribers (pagination needed for large lists)
        search_resp = requests.get(
            f"{LISTMONK_BASE_URL}/api/subscribers",
            auth=get_auth(),
            params={"per_page": 1000},
            timeout=10
        )
        search_resp.raise_for_status()
        subscribers = search_resp.json()["data"]["results"]

        existing = next((s for s in subscribers if s["email"].lower() == email.lower()), None)
        if existing:
            sub_id = existing["id"]
            old_attribs = existing.get("attribs", {}) or {}
            old_attribs.update(attribs)

            update_resp = requests.put(
                f"{LISTMONK_BASE_URL}/api/subscribers/{sub_id}",
                auth=get_auth(),
                json={
                    "email": email,
                    "name": name or existing.get("name", ""),
                    "attribs": old_attribs,
                    "lists": target_lists,
                    "status": "enabled"
                },
                timeout=10
            )
            update_resp.raise_for_status()
            return {"action": "updated", "id": sub_id}

    resp.raise_for_status()
    return {"action": "unknown"}


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    """handle subscription request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "no JSON body"}), 400

        # extract fields
        email = data.get("email", "").strip().lower()
        name = data.get("name", "").strip()
        cadence = data.get("cadence", "daily").strip().lower()
        subjects = data.get("subjects", [])
        honeypot = data.get("website", "")  # honeypot field

        # spam check: honeypot should be empty
        if honeypot:
            return jsonify({"ok": False, "error": "invalid request"}), 400

        # validate email
        if not email or not validate_email(email):
            return jsonify({"ok": False, "error": "invalid email"}), 400

        # validate cadence
        if cadence not in VALID_CADENCES:
            cadence = "daily"

        # validate subjects
        if isinstance(subjects, list):
            subjects = [s for s in subjects if s in VALID_SUBJECTS]
        else:
            subjects = []

        # load list IDs
        list_ids = load_list_ids()

        # upsert subscriber
        result = upsert_subscriber(email, name, cadence, subjects, list_ids)

        return jsonify({
            "ok": True,
            "action": result["action"],
            "message": "check your email to confirm subscription" if result["action"] == "created" else "preferences updated"
        })

    except requests.exceptions.RequestException as e:
        app.logger.error(f"listmonk API error: {e}")
        return jsonify({"ok": False, "error": "subscription service temporarily unavailable"}), 503
    except Exception as e:
        app.logger.error(f"subscribe error: {e}")
        return jsonify({"ok": False, "error": "internal error"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """health check"""
    return jsonify({"status": "ok", "service": "thebeakers-subscribe"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
