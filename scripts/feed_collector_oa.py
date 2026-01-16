#!/usr/bin/env python3
"""
feed_collector_oa.py - OA-first feed collector for TheBeakers

collects from:
- PMC (OAI-PMH)
- bioRxiv/medRxiv (RSS)
- arXiv (RSS)

outputs to archive table with pdf_url for direct download
"""

import argparse
import feedparser
import hashlib
import re
import sqlite3
import yaml
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, quote

# paths
SCRIPT_DIR = Path(__file__).parent
FEEDS_YAML = SCRIPT_DIR / "feeds.yaml"
DB_PATH = SCRIPT_DIR.parent / "data" / "articles.db"

# http headers
HEADERS = {
    "User-Agent": "TheBeakers/1.0 (educational platform; mailto:thebeakerscom@gmail.com)"
}


def ensure_archive_schema(conn: sqlite3.Connection) -> None:
    """ensure archive table exists with OA columns"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            headline TEXT,
            teaser TEXT,
            source TEXT,
            discipline TEXT,
            track TEXT,
            pdf_url TEXT,
            is_open_access INTEGER DEFAULT 1,
            oa_source TEXT,
            published_date TEXT,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_date TEXT
        )
    """)
    # add columns if missing (migration)
    for col, typedef in [
        ("pdf_url", "TEXT"),
        ("is_open_access", "INTEGER DEFAULT 1"),
        ("oa_source", "TEXT"),
        ("track", "TEXT"),
        ("published_date", "TEXT"),
        # new: source tier + cadence
        ("source_tier", "TEXT DEFAULT 'primary'"),  # primary | secondary
        ("discovered_from", "TEXT"),  # URL of secondary source
        ("primary_url", "TEXT"),  # resolved primary URL (DOI/arXiv/PMC)
        ("cadence", "TEXT"),  # daily | bi_daily | weekly
        ("publish_at", "TEXT"),  # scheduled publish timestamp
    ]:
        try:
            conn.execute(f"ALTER TABLE archive ADD COLUMN {col} {typedef}")
        except sqlite3.OperationalError:
            pass  # column exists
    conn.commit()


def load_feeds() -> Dict:
    """load feeds.yaml"""
    with open(FEEDS_YAML) as f:
        return yaml.safe_load(f)


def parse_biorxiv_rss(url: str, discipline: str) -> List[Dict]:
    """parse bioRxiv/medRxiv RSS feed"""
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:30]:  # limit per feed
            # extract DOI from link (stop before query string)
            link = entry.get("link", "")
            doi_match = re.search(r'10\.\d{4,}/[^\s?#]+', link)
            doi = doi_match.group(0) if doi_match else None

            # construct PDF URL
            pdf_url = None
            if doi:
                # biorxiv pattern: https://www.biorxiv.org/content/{doi}.full.pdf
                pdf_url = f"https://www.biorxiv.org/content/{doi}.full.pdf"

            # clean URL (remove query params like ?rss=1)
            clean_url = re.sub(r'\?.*$', '', link)

            articles.append({
                "url": clean_url,
                "headline": entry.get("title", ""),
                "teaser": entry.get("summary", "")[:1000] if entry.get("summary") else "",
                "source": "bioRxiv" if "biorxiv" in url else "medRxiv",
                "discipline": discipline,
                "track": "preprint",
                "pdf_url": pdf_url,
                "is_open_access": 1,
                "oa_source": "biorxiv",
                "published_date": entry.get("published", ""),
            })
    except Exception as e:
        print(f"  error parsing bioRxiv feed: {e}")
    return articles


def parse_biorxiv_api(start_date: str, end_date: str, categories: List[str] = None) -> List[Dict]:
    """fetch from bioRxiv API (better than RSS, no cloudflare)"""
    articles = []
    url = f"https://api.biorxiv.org/details/biorxiv/{start_date}/{end_date}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        total = data.get("messages", [{}])[0].get("total", 0)
        print(f"    API returned {total} preprints")

        for item in data.get("collection", []):
            category = item.get("category", "").lower()

            # filter by category if specified
            if categories and not any(c.lower() in category for c in categories):
                continue

            doi = item.get("doi", "")

            # map category to discipline
            discipline = "biology"  # default
            if "biochem" in category:
                discipline = "chemistry"
            elif "bioinformatics" in category or "systems" in category:
                discipline = "ai"

            articles.append({
                "url": f"https://doi.org/{doi}",
                "headline": item.get("title", ""),
                "teaser": item.get("abstract", "")[:1000] if item.get("abstract") else "",
                "source": "bioRxiv",
                "discipline": discipline,
                "track": "preprint",
                "pdf_url": None,  # let Unpaywall find it
                "is_open_access": 1,
                "oa_source": "biorxiv_api",
                "published_date": item.get("date", ""),
            })

    except Exception as e:
        print(f"  error fetching bioRxiv API: {e}")

    return articles


def parse_arxiv_rss(url: str, discipline: str) -> List[Dict]:
    """parse arXiv RSS feed"""
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:30]:
            # extract arXiv ID from link (e.g., http://arxiv.org/abs/2401.12345)
            arxiv_id = None
            link = entry.get("link", "")
            match = re.search(r'arxiv\.org/abs/([^\s]+)', link)
            if match:
                arxiv_id = match.group(1)

            # construct PDF URL (arXiv direct works)
            pdf_url = None
            if arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            articles.append({
                "url": link,
                "headline": entry.get("title", "").replace("\n", " "),
                "teaser": entry.get("summary", "")[:1000] if entry.get("summary") else "",
                "source": "arXiv",
                "discipline": discipline,
                "track": "preprint",
                "pdf_url": pdf_url,
                "is_open_access": 1,
                "oa_source": "arxiv",
                "published_date": entry.get("published", ""),
            })
    except Exception as e:
        print(f"  error parsing arXiv feed: {e}")
    return articles


def try_crossref_doi(title: str) -> Optional[str]:
    """resolve DOI from title via Crossref API"""
    if not title or len(title) < 10:
        return None

    # crossref polite pool - include email
    url = f"https://api.crossref.org/works?query.title={quote(title[:200])}&rows=1&mailto=thebeakerscom@gmail.com"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("message", {}).get("items", [])
            if items:
                doi = items[0].get("DOI")
                # verify title similarity (basic check to avoid false matches)
                api_title = items[0].get("title", [""])[0].lower() if items[0].get("title") else ""
                if title.lower()[:50] in api_title or api_title[:50] in title.lower():
                    return doi
    except Exception:
        pass  # fail silently, DOI is optional
    return None


def parse_publisher_rss(url: str, discipline: str, source_name: str) -> List[Dict]:
    """parse generic publisher RSS feed (metadata-only, PDF via Unpaywall)"""
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:30]:
            link = entry.get("link", "")

            # extract DOI if present
            doi = None
            doi_match = re.search(r'10\.\d{4,}/[^\s?#]+', link)
            if doi_match:
                doi = doi_match.group(0)
            else:
                # try Crossref lookup for entries without DOI in URL
                entry_title = entry.get("title", "")
                doi = try_crossref_doi(entry_title)
                if doi:
                    link = f"https://doi.org/{doi}"  # use canonical DOI URL

            articles.append({
                "url": link,
                "headline": entry.get("title", "").replace("\n", " "),
                "teaser": entry.get("summary", "")[:1000] if entry.get("summary") else "",
                "source": source_name,
                "discipline": discipline,
                "track": "peer_reviewed",
                "pdf_url": None,  # PDF via Unpaywall, not direct
                "is_open_access": 0,  # assume paywalled until Unpaywall confirms
                "oa_source": "publisher",
                "published_date": entry.get("published", ""),
            })
    except Exception as e:
        print(f"  error parsing {source_name} feed: {e}")
    return articles


def parse_pmc_oai(url: str, discipline: str) -> List[Dict]:
    """parse PMC OAI-PMH response"""
    articles = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        # parse XML
        root = ET.fromstring(resp.text)
        ns = {
            "oai": "http://www.openarchives.org/OAI/2.0/",
            "pmc": "https://jats.nlm.nih.gov/ns/archiving/1.3/"
        }

        for record in root.findall(".//oai:record", ns)[:30]:
            try:
                metadata = record.find(".//oai:metadata", ns)
                if metadata is None:
                    continue

                # extract article info (PMC format varies)
                article = metadata.find(".//{*}article")
                if article is None:
                    continue

                # get title
                title_elem = article.find(".//{*}article-title")
                title = title_elem.text if title_elem is not None else ""

                # get abstract
                abstract_elem = article.find(".//{*}abstract")
                abstract = ""
                if abstract_elem is not None:
                    abstract = " ".join(abstract_elem.itertext())[:1000]

                # get PMC ID
                pmc_id = None
                for id_elem in article.findall(".//{*}article-id"):
                    if id_elem.get("pub-id-type") == "pmc":
                        pmc_id = id_elem.text

                # construct URLs
                url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/" if pmc_id else ""
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/" if pmc_id else None

                if url and title:
                    articles.append({
                        "url": url,
                        "headline": title,
                        "teaser": abstract,
                        "source": "PMC",
                        "discipline": discipline,
                        "track": "peer_reviewed",
                        "pdf_url": pdf_url,
                        "is_open_access": 1,
                        "oa_source": "pmc",
                        "published_date": "",
                    })
            except Exception as e:
                continue

    except Exception as e:
        print(f"  error parsing PMC OAI: {e}")
    return articles


def collect_from_source(source_type: str, feeds_config: Dict, discipline_filter: Optional[str] = None) -> List[Dict]:
    """collect articles from a source type"""
    all_articles = []

    if source_type not in feeds_config:
        print(f"source '{source_type}' not in config")
        return []

    source_feeds = feeds_config[source_type]

    # handle paywalled sources (skip fulltext)
    if source_feeds.get("skip_fulltext"):
        print(f"  skipping paywalled source: {source_type}")
        return []

    # special handling for bioRxiv API
    if source_type == "biorxiv_api":
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        categories = source_feeds.get("categories", [])
        print(f"  bioRxiv API: {start_date} to {end_date}")
        return parse_biorxiv_api(start_date, end_date, categories)

    # get pdf_method for this source (direct | unpaywall | none)
    pdf_method = source_feeds.get("pdf_method", "direct")

    for discipline, feed_list in source_feeds.items():
        if discipline_filter and discipline != discipline_filter:
            continue

        if not isinstance(feed_list, list):
            continue

        for feed in feed_list:
            name = feed.get("name", "unknown")
            url = feed.get("url", "")
            feed_type = feed.get("type", "rss")

            print(f"  [{discipline}] {name}...")

            if feed_type == "rss":
                if "biorxiv" in url or "medrxiv" in url:
                    articles = parse_biorxiv_rss(url, discipline)
                elif "arxiv" in url:
                    articles = parse_arxiv_rss(url, discipline)
                elif pdf_method == "unpaywall":
                    # publisher feeds: metadata-only, PDF via Unpaywall
                    articles = parse_publisher_rss(url, discipline, name)
                else:
                    # generic RSS (fallback to arXiv parser)
                    articles = parse_arxiv_rss(url, discipline)
            elif feed_type == "oai-pmh":
                articles = parse_pmc_oai(url, discipline)
            else:
                print(f"    unknown feed type: {feed_type}")
                continue

            print(f"    found {len(articles)} articles")
            all_articles.extend(articles)

    return all_articles


def save_articles(articles: List[Dict], conn: sqlite3.Connection, dry_run: bool = False) -> Dict:
    """save articles to archive table"""
    stats = {"new": 0, "existing": 0, "errors": 0}

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
            print(f"    [dry-run] would insert: {article['headline'][:50]}...")
            stats["new"] += 1
            continue

        try:
            conn.execute("""
                INSERT INTO archive (url, headline, teaser, source, discipline, track,
                                    pdf_url, is_open_access, oa_source, published_date, approved_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article["url"],
                article.get("headline", ""),
                article.get("teaser", ""),
                article.get("source", ""),
                article.get("discipline", ""),
                article.get("track", ""),
                article.get("pdf_url"),
                article.get("is_open_access", 1),
                article.get("oa_source", ""),
                article.get("published_date", ""),
                datetime.now().isoformat(),  # auto-approve OA articles
            ))
            stats["new"] += 1
        except Exception as e:
            print(f"    error inserting {url[:50]}: {e}")
            stats["errors"] += 1

    conn.commit()
    return stats


def run_collection(
    sources: List[str] = None,
    discipline: str = None,
    limit: int = 100,
    dry_run: bool = False
) -> Dict:
    """run feed collection"""

    if sources is None:
        sources = ["pmc", "biorxiv", "medrxiv", "arxiv"]

    feeds_config = load_feeds()
    conn = sqlite3.connect(DB_PATH)
    ensure_archive_schema(conn)

    print(f"=== OA FEED COLLECTION ===")
    print(f"sources: {sources}")
    print(f"discipline: {discipline or 'all'}")

    all_articles = []

    for source in sources:
        print(f"\n>>> {source.upper()}")
        articles = collect_from_source(source, feeds_config, discipline)
        all_articles.extend(articles)

    # dedupe by URL
    seen = set()
    unique_articles = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique_articles.append(a)

    print(f"\n>>> SAVING")
    print(f"total unique: {len(unique_articles)}")

    # limit
    if len(unique_articles) > limit:
        unique_articles = unique_articles[:limit]
        print(f"limited to: {limit}")

    stats = save_articles(unique_articles, conn, dry_run)

    conn.close()

    print(f"\n=== SUMMARY ===")
    print(f"new: {stats['new']}")
    print(f"existing: {stats['existing']}")
    print(f"errors: {stats['errors']}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="collect OA articles from PMC, bioRxiv, arXiv")
    parser.add_argument("--sources", default="pmc,biorxiv,arxiv",
                        help="comma-separated sources (pmc,biorxiv,medrxiv,arxiv)")
    parser.add_argument("--discipline", help="filter by discipline")
    parser.add_argument("--limit", type=int, default=100, help="max articles to collect")
    parser.add_argument("--dry-run", action="store_true", help="don't save to DB")

    args = parser.parse_args()
    sources = [s.strip() for s in args.sources.split(",")]

    run_collection(sources, args.discipline, args.limit, args.dry_run)


if __name__ == "__main__":
    main()
