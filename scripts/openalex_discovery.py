#!/usr/bin/env python3
"""
openalex_discovery.py - discover papers via OpenAlex API

use for:
- topic/keyword search
- citation traversal
- finding trending papers

then resolve DOIs via Unpaywall for PDF access
"""

import argparse
import json
import requests
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

# config
DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
OPENALEX_EMAIL = "thebeakerscom@gmail.com"

HEADERS = {
    "User-Agent": f"TheBeakers/1.0 (mailto:{OPENALEX_EMAIL})"
}

# discipline -> OpenAlex concept IDs (top-level)
CONCEPT_MAP = {
    "biology": "C86803240",      # biology
    "chemistry": "C185592680",   # chemistry
    "physics": "C121332964",     # physics
    "ai": "C154945302",          # artificial intelligence
    "engineering": "C127413603", # engineering
    "mathematics": "C33923547",  # mathematics
}


def search_openalex(
    query: str = None,
    concept_id: str = None,
    from_date: str = None,
    filter_oa: bool = False,
    limit: int = 50
) -> List[Dict]:
    """
    search OpenAlex for papers

    args:
        query: text search (title/abstract)
        concept_id: OpenAlex concept ID to filter by
        from_date: only papers from this date (YYYY-MM-DD)
        filter_oa: only return open access papers
        limit: max results
    """
    base_url = "https://api.openalex.org/works"

    filters = []
    if concept_id:
        filters.append(f"concepts.id:{concept_id}")
    if from_date:
        filters.append(f"from_publication_date:{from_date}")
    if filter_oa:
        filters.append("is_oa:true")

    params = {
        "mailto": OPENALEX_EMAIL,
        "per_page": min(limit, 200),
        "sort": "publication_date:desc",
    }

    if query:
        params["search"] = query
    if filters:
        params["filter"] = ",".join(filters)

    articles = []
    try:
        resp = requests.get(base_url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for work in data.get("results", []):
            doi = work.get("doi", "").replace("https://doi.org/", "")
            if not doi:
                continue

            # map primary topic to discipline
            discipline = "biology"  # default
            primary_topic = work.get("primary_topic", {})
            if primary_topic:
                domain = primary_topic.get("domain", {}).get("display_name", "").lower()
                if "chemistry" in domain or "chemical" in domain:
                    discipline = "chemistry"
                elif "physics" in domain:
                    discipline = "physics"
                elif "computer" in domain or "artificial" in domain:
                    discipline = "ai"
                elif "engineering" in domain:
                    discipline = "engineering"
                elif "math" in domain:
                    discipline = "mathematics"

            articles.append({
                "url": f"https://doi.org/{doi}",
                "doi": doi,
                "headline": work.get("title", ""),
                "teaser": work.get("abstract", "") or "",
                "source": work.get("primary_location", {}).get("source", {}).get("display_name", "OpenAlex"),
                "discipline": discipline,
                "track": "peer_reviewed",
                "is_open_access": 1 if work.get("open_access", {}).get("is_oa") else 0,
                "oa_source": "openalex",
                "published_date": work.get("publication_date", ""),
                "cited_by_count": work.get("cited_by_count", 0),
            })

    except Exception as e:
        print(f"OpenAlex error: {e}")

    return articles


def discover_trending(discipline: str, days: int = 7, limit: int = 20) -> List[Dict]:
    """find trending papers in a discipline from the last N days"""
    concept_id = CONCEPT_MAP.get(discipline)
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    print(f"Searching OpenAlex: {discipline}, from {from_date}")
    articles = search_openalex(
        concept_id=concept_id,
        from_date=from_date,
        filter_oa=True,  # only OA for now
        limit=limit
    )

    # sort by citations (trending)
    articles.sort(key=lambda x: x.get("cited_by_count", 0), reverse=True)
    return articles


def save_to_archive(articles: List[Dict], dry_run: bool = False) -> Dict:
    """save discovered articles to archive table"""
    conn = sqlite3.connect(DB_PATH)

    stats = {"new": 0, "existing": 0}

    for article in articles:
        url = article.get("url")
        if not url:
            continue

        # check if exists
        existing = conn.execute("SELECT 1 FROM archive WHERE url = ?", (url,)).fetchone()
        if existing:
            stats["existing"] += 1
            continue

        if dry_run:
            print(f"  [dry-run] would insert: {article['headline'][:50]}...")
            stats["new"] += 1
            continue

        try:
            conn.execute("""
                INSERT INTO archive (url, headline, teaser, source, discipline, track,
                                    is_open_access, oa_source, published_date, approved_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article["url"],
                article.get("headline", ""),
                article.get("teaser", "")[:1000],
                article.get("source", ""),
                article.get("discipline", ""),
                article.get("track", "peer_reviewed"),
                article.get("is_open_access", 0),
                article.get("oa_source", "openalex"),
                article.get("published_date", ""),
                datetime.now().isoformat(),
            ))
            stats["new"] += 1
        except Exception as e:
            print(f"  error: {e}")

    conn.commit()
    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="discover papers via OpenAlex")
    parser.add_argument("--discipline", default="biology",
                        help="discipline to search (biology, chemistry, physics, ai, engineering, mathematics)")
    parser.add_argument("--query", help="text search query")
    parser.add_argument("--days", type=int, default=7, help="papers from last N days")
    parser.add_argument("--limit", type=int, default=20, help="max papers to fetch")
    parser.add_argument("--oa-only", action="store_true", help="only open access papers")
    parser.add_argument("--save", action="store_true", help="save to archive table")
    parser.add_argument("--dry-run", action="store_true", help="don't actually save")

    args = parser.parse_args()

    if args.query:
        print(f"Searching: {args.query}")
        articles = search_openalex(
            query=args.query,
            from_date=(datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d"),
            filter_oa=args.oa_only,
            limit=args.limit
        )
    else:
        articles = discover_trending(args.discipline, args.days, args.limit)

    print(f"\nFound {len(articles)} articles:")
    for a in articles[:10]:
        oa = "OA" if a.get("is_open_access") else "closed"
        print(f"  [{oa}] {a['headline'][:60]}... ({a.get('cited_by_count', 0)} cites)")

    if args.save:
        stats = save_to_archive(articles, args.dry_run)
        print(f"\nSaved: new={stats['new']}, existing={stats['existing']}")


if __name__ == "__main__":
    main()
