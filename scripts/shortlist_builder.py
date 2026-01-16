#!/usr/bin/env python3
"""
Build shortlist with credibility labels + simple scoring.
Outputs: data/shortlist.json

This is a v1 heuristic scorer. You can tighten later.
"""

import json
from datetime import datetime
from pathlib import Path

BEAKERS_DIR = Path(__file__).parent.parent
DATA_DIR = BEAKERS_DIR / "data"

PENDING = DATA_DIR / "pending_articles.json"
RESOLUTION = DATA_DIR / "resolution.json"
OUT = DATA_DIR / "shortlist.json"

ACCESS_SCORE = {
    "oa_pdf": 1.0,
    "accepted_ms": 0.8,
    "preprint": 0.7,
    "metadata_only": 0.0
}

def value_score(item: dict) -> float:
    # v1: use source_type as a proxy for "story-worthiness"
    # review/education > high_impact for your use-case
    st = item.get("source_type")
    deep = 1.0 if st in ("review", "education") else 0.6
    oa = 1.0 if item.get("open_access") else 0.2
    has_doi = 1.0 if item.get("doi") else 0.3
    teaser = item.get("teaser","")
    clarity = 1.0 if len(teaser) >= 120 else 0.5

    # weighted sum (0..1)
    v = 0.40*deep + 0.25*clarity + 0.20*oa + 0.15*has_doi
    return max(0.0, min(1.0, v))

def feasibility_score(item: dict, access_level: str) -> float:
    a = ACCESS_SCORE.get(access_level, 0.0)
    # parseability proxy: having a DOI and teaser helps
    has_doi = 1.0 if item.get("doi") else 0.3
    teaser = item.get("teaser","")
    parseable = 1.0 if len(teaser) >= 80 else 0.5
    f = 0.60*a + 0.25*parseable + 0.15*has_doi
    return max(0.0, min(1.0, f))

def main():
    if not PENDING.exists():
        raise SystemExit("pending_articles.json not found")
    if not RESOLUTION.exists():
        raise SystemExit("resolution.json not found (run access_resolver first)")

    pending = json.loads(PENDING.read_text())
    res = json.loads(RESOLUTION.read_text()).get("items", {})

    shortlisted = []
    rejected = []

    for discipline, buckets in pending.get("disciplines", {}).items():
        for source_type, items in buckets.items():
            for it in items:
                key = it.get("url") or f"{it.get('headline','')}-{discipline}"
                r = res.get(key, {})
                access_level = r.get("access_level", "metadata_only")
                best_url = r.get("best_url", it.get("url",""))

                v = value_score(it) * 100.0
                f = feasibility_score(it, access_level) * 100.0

                # thresholds (your stated policy)
                ok = (v >= 70.0 and f >= 70.0)

                record = {
                    "discipline": discipline,
                    "headline": it.get("headline",""),
                    "source": it.get("source",""),
                    "source_type": it.get("source_type",""),
                    "url": it.get("url",""),
                    "doi": it.get("doi",""),
                    "review_status": it.get("review_status","peer_reviewed"),
                    "publish_label": it.get("publish_label","Peer-Reviewed"),
                    "open_access_hint": bool(it.get("open_access")),
                    "access_level": access_level,
                    "best_url": best_url,
                    "scores": {
                        "value": round(v, 1),
                        "feasibility": round(f, 1)
                    }
                }

                (shortlisted if ok else rejected).append(record)

    # sort best-first
    shortlisted.sort(key=lambda x: (x["scores"]["value"] + x["scores"]["feasibility"]), reverse=True)

    out = {
        "built": datetime.now().isoformat(),
        "selected_count": len(shortlisted),
        "rejected_count": len(rejected),
        "selected": shortlisted,
        "rejected": rejected[:200]  # keep file sane
    }

    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote: {OUT}")
    print(f"selected: {len(shortlisted)}  rejected: {len(rejected)}")

if __name__ == "__main__":
    main()

