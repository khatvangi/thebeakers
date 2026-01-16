#!/usr/bin/env python3
"""
secondary_discovery.py - collect from secondary sources → resolve to primary

RULE: never run truth pipeline on secondary article
      always resolve to DOI/arXiv/PMCID and create primary record

workflow:
1. collect from secondary RSS (ScienceDaily, MIT Tech Review, etc.)
2. scrape each article for DOI/arXiv/PMCID links
3. if found: create primary record with discovered_from=secondary_url
4. if not found: skip (or try Crossref title match)
"""

import argparse
import feedparser
import re
import requests
import sqlite3
import yaml
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

# paths
SCRIPT_DIR = Path(__file__).parent
FEEDS_YAML = SCRIPT_DIR / "feeds.yaml"
DB_PATH = SCRIPT_DIR.parent / "data" / "articles.db"

# headers
HEADERS = {
    "User-Agent": "TheBeakers/1.0 (educational platform; mailto:thebeakerscom@gmail.com)"
}

# patterns for finding primary sources
DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s"\'<>\]]+')
ARXIV_PATTERN = re.compile(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)')
PMCID_PATTERN = re.compile(r'PMC\d{7,}')
PMID_PATTERN = re.compile(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)')


def load_feeds() -> Dict:
    """load feeds.yaml"""
    with open(FEEDS_YAML) as f:
        return yaml.safe_load(f)


def scrape_page_for_primary(url: str) -> Optional[Dict]:
    """scrape a secondary article page for primary source links"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()

        # look for DOI
        dois = DOI_PATTERN.findall(text)
        # also check href attributes
        for a in soup.find_all("a", href=True):
            href = a["href"]
            doi_in_href = DOI_PATTERN.search(href)
            if doi_in_href:
                dois.append(doi_in_href.group(0))

        # clean DOIs (remove trailing punctuation)
        dois = [re.sub(r'[.,;:)\]]+$', '', d) for d in dois]
        dois = list(set(dois))  # dedupe

        if dois:
            # prefer the first valid DOI
            for doi in dois:
                if len(doi) > 10 and "/" in doi:
                    return {
                        "type": "doi",
                        "id": doi,
                        "url": f"https://doi.org/{doi}"
                    }

        # look for arXiv
        arxiv_matches = ARXIV_PATTERN.findall(text)
        for a in soup.find_all("a", href=True):
            arxiv_in_href = ARXIV_PATTERN.search(a["href"])
            if arxiv_in_href:
                arxiv_matches.append(arxiv_in_href.group(1))

        if arxiv_matches:
            arxiv_id = arxiv_matches[0]
            return {
                "type": "arxiv",
                "id": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}"
            }

        # look for PMC
        pmcids = PMCID_PATTERN.findall(text)
        if pmcids:
            pmcid = pmcids[0]
            return {
                "type": "pmc",
                "id": pmcid,
                "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            }

        # look for PubMed
        pmids = PMID_PATTERN.findall(text)
        if pmids:
            pmid = pmids[0]
            # try to resolve PMID to DOI via NCBI
            return {
                "type": "pubmed",
                "id": pmid,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }

        return None

    except Exception as e:
        print(f"    error scraping {url[:50]}: {e}")
        return None


def try_crossref_title_match(title: str) -> Optional[str]:
    """try to find DOI via Crossref title search"""
    if not title or len(title) < 15:
        return None

    url = f"https://api.crossref.org/works?query.title={quote(title[:200])}&rows=1&mailto=thebeakerscom@gmail.com"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("message", {}).get("items", [])
            if items:
                doi = items[0].get("DOI")
                api_title = items[0].get("title", [""])[0].lower() if items[0].get("title") else ""
                # verify similarity
                if title.lower()[:40] in api_title or api_title[:40] in title.lower():
                    return doi
    except Exception:
        pass
    return None


def infer_discipline(title: str, teaser: str, source_category: str) -> str:
    """infer discipline from content and source category"""
    text = (title + " " + teaser).lower()

    # explicit category mapping
    if source_category in ["biology", "health"]:
        return "biology"
    if source_category == "physics":
        return "physics"
    if source_category in ["ai", "tech"]:
        return "ai"

    # keyword-based inference
    if any(w in text for w in ["gene", "protein", "cell", "brain", "cancer", "biology", "medical"]):
        return "biology"
    if any(w in text for w in ["quantum", "particle", "physics", "laser", "photon"]):
        return "physics"
    if any(w in text for w in ["ai", "machine learning", "neural network", "algorithm", "robot"]):
        return "ai"
    if any(w in text for w in ["chemistry", "molecule", "compound", "catalyst", "reaction"]):
        return "chemistry"
    if any(w in text for w in ["engineer", "material", "battery", "energy", "device"]):
        return "engineering"
    if any(w in text for w in ["math", "equation", "theorem", "algorithm"]):
        return "mathematics"

    return "biology"  # default


def collect_secondary_feed(feed_config: Dict, category: str) -> List[Dict]:
    """collect articles from a single secondary feed"""
    articles = []
    url = feed_config.get("url", "")
    name = feed_config.get("name", "unknown")

    print(f"    [{name}]...")

    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:20]:  # limit per feed
            link = entry.get("link", "")
            title = entry.get("title", "").replace("\n", " ").strip()
            teaser = entry.get("summary", "")[:500] if entry.get("summary") else ""

            if not link or not title:
                continue

            articles.append({
                "secondary_url": link,
                "secondary_headline": title,
                "secondary_teaser": teaser,
                "secondary_source": name,
                "category": category,
                "published_date": entry.get("published", ""),
            })

        print(f"      found {len(articles)} entries")

    except Exception as e:
        print(f"      error: {e}")

    return articles


def resolve_to_primary(article: Dict) -> Optional[Dict]:
    """resolve secondary article to primary source"""
    url = article["secondary_url"]

    # first, try scraping the page
    primary = scrape_page_for_primary(url)

    if not primary:
        # fallback: try Crossref title match
        doi = try_crossref_title_match(article["secondary_headline"])
        if doi:
            primary = {
                "type": "doi",
                "id": doi,
                "url": f"https://doi.org/{doi}"
            }

    return primary


def save_discovered_article(
    conn: sqlite3.Connection,
    secondary: Dict,
    primary: Dict,
    dry_run: bool = False
) -> bool:
    """save discovered article to archive as primary with discovered_from"""
    primary_url = primary["url"]

    # check if primary already exists
    existing = conn.execute("SELECT 1 FROM archive WHERE url = ?", (primary_url,)).fetchone()
    if existing:
        return False  # already have this primary

    discipline = infer_discipline(
        secondary["secondary_headline"],
        secondary["secondary_teaser"],
        secondary["category"]
    )

    if dry_run:
        print(f"      [dry-run] would insert: {primary_url[:50]}...")
        return True

    try:
        conn.execute("""
            INSERT INTO archive (
                url, headline, teaser, source, discipline, track,
                is_open_access, oa_source, published_date, approved_date,
                source_tier, discovered_from, primary_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            primary_url,
            secondary["secondary_headline"],
            secondary["secondary_teaser"],
            secondary["secondary_source"],
            discipline,
            "peer_reviewed" if primary["type"] == "doi" else "preprint",
            0,  # assume not OA until Unpaywall confirms
            "secondary_discovery",
            secondary["published_date"],
            datetime.now().isoformat(),
            "primary",  # this is the primary record
            secondary["secondary_url"],  # discovered from secondary
            primary_url,
        ))
        return True
    except Exception as e:
        print(f"      error saving: {e}")
        return False


def run_secondary_discovery(
    categories: List[str] = None,
    limit: int = 50,
    dry_run: bool = False
) -> Dict:
    """run secondary discovery collection"""
    feeds_config = load_feeds()

    if "secondary" not in feeds_config:
        print("no secondary feeds configured")
        return {"discovered": 0, "skipped": 0}

    secondary_feeds = feeds_config["secondary"]

    conn = sqlite3.connect(DB_PATH)

    # ensure schema has new columns
    from feed_collector_oa import ensure_archive_schema
    ensure_archive_schema(conn)

    print("=== SECONDARY DISCOVERY ===")

    all_articles = []

    # collect from secondary feeds
    for category, feed_list in secondary_feeds.items():
        if categories and category not in categories:
            continue

        if not isinstance(feed_list, list):
            continue

        print(f"\n>>> {category.upper()}")

        for feed_config in feed_list:
            articles = collect_secondary_feed(feed_config, category)
            all_articles.extend(articles)

    print(f"\n>>> RESOLVING {len(all_articles)} articles to primary...")

    stats = {"discovered": 0, "skipped": 0, "no_primary": 0}

    for i, article in enumerate(all_articles[:limit]):
        print(f"  [{i+1}/{min(len(all_articles), limit)}] {article['secondary_headline'][:50]}...")

        primary = resolve_to_primary(article)

        if primary:
            print(f"      -> {primary['type']}: {primary['url'][:50]}...")
            saved = save_discovered_article(conn, article, primary, dry_run)
            if saved:
                stats["discovered"] += 1
            else:
                stats["skipped"] += 1  # already exists
        else:
            print(f"      -> no primary found")
            stats["no_primary"] += 1

    if not dry_run:
        conn.commit()
    conn.close()

    print(f"\n=== SUMMARY ===")
    print(f"discovered: {stats['discovered']}")
    print(f"skipped (existing): {stats['skipped']}")
    print(f"no primary found: {stats['no_primary']}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="discover articles from secondary sources")
    parser.add_argument("--categories", help="comma-separated categories (general,tech,biology,physics,ai)")
    parser.add_argument("--limit", type=int, default=50, help="max articles to process")
    parser.add_argument("--dry-run", action="store_true", help="don't save to DB")

    args = parser.parse_args()
    categories = [c.strip() for c in args.categories.split(",")] if args.categories else None

    run_secondary_discovery(categories, args.limit, args.dry_run)


if __name__ == "__main__":
    main()
