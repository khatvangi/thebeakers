#!/usr/bin/env python3
"""
Resolve legal access for collected items.
Outputs: data/resolution.json

Rules:
- Never scrape paywalls.
- Use Unpaywall if DOI exists (requires UNPAYWALL_EMAIL env var).
- Always accept preprint links as legal.
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import urllib.request

BEAKERS_DIR = Path(__file__).parent.parent
DATA_DIR = BEAKERS_DIR / "data"
PENDING = DATA_DIR / "pending_articles.json"
OUT = DATA_DIR / "resolution.json"

UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "").strip()

def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    doi = doi.replace("https://dx.doi.org/", "").replace("http://dx.doi.org/", "")
    doi = doi.strip()
    # strip junk after whitespace
    doi = doi.split()[0]
    return doi

def is_preprint_url(url: str) -> bool:
    u = (url or "").lower()
    return any(x in u for x in ["arxiv.org", "biorxiv.org", "chemrxiv.org", "medrxiv.org"])

def fetch_json(url: str, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "thebeakers/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def unpaywall_lookup(doi: str):
    if not UNPAYWALL_EMAIL:
        return None
    doi_q = quote(doi, safe="")
    url = f"https://api.unpaywall.org/v2/{doi_q}?email={quote(UNPAYWALL_EMAIL)}"
    try:
        return fetch_json(url)
    except Exception:
        return None

def resolve_one(item: dict) -> dict:
    url = item.get("url", "")
    doi = normalize_doi(item.get("doi", ""))

    # Preprint URLs are legal and directly usable
    if is_preprint_url(url):
        return {
            "doi": doi,
            "access_level": "preprint",
            "best_url": url,
            "evidence": "preprint_url"
        }

    if not doi:
        # no DOI, no safe resolver: metadata-only
        return {
            "doi": "",
            "access_level": "metadata_only",
            "best_url": url,
            "evidence": "no_doi"
        }

    data = unpaywall_lookup(doi)
    if not data:
        # without unpaywall email or lookup failure, fall back to metadata-only
        return {
            "doi": doi,
            "access_level": "metadata_only",
            "best_url": f"https://doi.org/{doi}",
            "evidence": "unpaywall_unavailable"
        }

    best = data.get("best_oa_location") or {}
    oa_url = best.get("url_for_pdf") or best.get("url")

    if oa_url:
        host = (oa_url or "").lower()
        # classify loosely
        if best.get("url_for_pdf"):
            level = "oa_pdf"
        else:
            # could be html OA or repository
            level = "accepted_ms" if best.get("host_type") == "repository" else "oa_pdf"
        return {
            "doi": doi,
            "access_level": level,
            "best_url": oa_url,
            "evidence": f"unpaywall:{best.get('host_type','unknown')}"
        }

    # no OA found
    return {
        "doi": doi,
        "access_level": "metadata_only",
        "best_url": f"https://doi.org/{doi}",
        "evidence": "no_oa_found"
    }

def main():
    if not PENDING.exists():
        raise SystemExit("pending_articles.json not found. Run feed_collector first.")

    data = json.loads(PENDING.read_text())
    out = {
        "resolved": datetime.now().isoformat(),
        "unpaywall_email_set": bool(UNPAYWALL_EMAIL),
        "items": {}
    }

    # flatten all collected items
    for discipline, buckets in data.get("disciplines", {}).items():
        for source_type, items in buckets.items():
            for it in items:
                key = it.get("url") or f"{it.get('headline','')}-{discipline}"
                out["items"][key] = resolve_one(it)
                # polite rate limit if using unpaywall
                if UNPAYWALL_EMAIL:
                    time.sleep(0.25)

    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote: {OUT}")

if __name__ == "__main__":
    main()

