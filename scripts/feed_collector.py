#!/usr/bin/env python3
"""
The Beakers Feed Collector v2
Curated article collection for STEM disciplines

Strategy:
- REVIEW journals -> Deep Dive candidates (NotebookLM)
- HIGH_IMPACT journals -> Regular summaries (Ollama)
- EDUCATION journals -> Teaching resources
"""

import feedparser
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
import html
import socket

# Set network timeout
socket.setdefaulttimeout(15)

# Paths
BEAKERS_DIR = Path(__file__).parent.parent
DATA_DIR = BEAKERS_DIR / "data"
DB_PATH = DATA_DIR / "articles.db"

# =============================================================================
# CURATED FEEDS - Quality over quantity
# =============================================================================
#
# review: Review articles for Deep Dive (NotebookLM treatment)
# high_impact: Top journals for regular summaries (Ollama)
# education: Teaching-focused articles
# =============================================================================

# Open Access sources - PDFs freely available
OPEN_ACCESS_SOURCES = {
    "eLife", "PLOS", "arXiv", "Nature Communications", "Scientific Reports",
    "MDPI", "Frontiers", "PeerJ", "BMC", "Annual Reviews",  # Annual Reviews often OA after 1 year
    "JMLR", "arXiv cs.LG", "arXiv cs.AI", "bioRxiv", "medRxiv"
}

FEEDS = {
    "chemistry": {
        "review": [
            # Review journals - perfect for Deep Dive
            ("Chemical Reviews", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=chreay"),  # IF 62
            ("Chem Society Reviews", "https://pubs.rsc.org/en/journals/journalissues/cs?_type=rss"),  # IF 46
            ("Acc. Chemical Research", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=achre4"),  # IF 24
        ],
        "high_impact": [
            # Top research journals
            ("JACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jacsat"),  # IF 15
            ("Nature Chemistry", "https://www.nature.com/nchem.rss"),  # IF 24
            ("Angewandte Chemie", "https://onlinelibrary.wiley.com/feed/15213773/most-recent"),  # IF 16
            ("ACS Central Science", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=acscii"),  # IF 18
        ],
        "education": [
            ("J. Chem. Education", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jceda8"),
        ]
    },

    "physics": {
        "review": [
            # Review journals - perfect for Deep Dive
            ("Reviews of Modern Physics", "https://feeds.aps.org/rss/recent/rmp.xml"),  # IF 54
            ("Physics Reports", "https://rss.sciencedirect.com/publication/science/03701573"),  # IF 30
            ("Reports on Progress in Physics", "https://iopscience.iop.org/journal/rss/0034-4885"),  # IF 19
        ],
        "high_impact": [
            # Top research journals
            ("Nature Physics", "https://www.nature.com/nphys.rss"),  # IF 19
            ("Physical Review Letters", "https://feeds.aps.org/rss/recent/prl.xml"),  # IF 9
            ("Physical Review X", "https://feeds.aps.org/rss/recent/prx.xml"),  # IF 12
        ],
        "education": [
            ("American J. Physics", "https://pubs.aip.org/rss/site_1000029/1000029.xml"),
            ("The Physics Teacher", "https://pubs.aip.org/rss/site_1000031/1000031.xml"),
        ]
    },

    "biology": {
        "review": [
            # Review journals - perfect for Deep Dive
            ("eLife", "https://elifesciences.org/rss/recent.xml"),  # OPEN ACCESS! Great reviews
            ("Nature Rev Genetics", "https://www.nature.com/nrg.rss"),  # IF 60
            ("Nature Rev Mol Cell Bio", "https://www.nature.com/nrm.rss"),  # IF 94
            ("Annual Rev Biochemistry", "https://www.annualreviews.org/rss/content/journals/biochem?fmt=rss"),  # IF 25
            ("Trends in Biochem Sci", "https://www.cell.com/trends/biochemical-sciences/rss"),  # IF 14
        ],
        "high_impact": [
            # Top research journals
            ("Nature", "https://www.nature.com/nature.rss"),  # IF 50
            ("Cell", "https://www.cell.com/cell/rss"),  # IF 64
            ("Science", "https://www.science.org/rss/news_current.xml"),  # IF 56
        ],
        "education": [
            ("CBE Life Sci Education", "https://www.lifescied.org/rss/recent.xml"),
        ]
    },

    "mathematics": {
        "review": [
            # Review journals - perfect for Deep Dive
            ("SIAM Review", "https://epubs.siam.org/action/showFeed?type=etoc&feed=rss&jc=siread"),  # IF 10
            ("Bulletin of the AMS", "https://www.ams.org/rss/bull.rss"),  # Survey articles
            ("Notices of the AMS", "https://www.ams.org/rss/notices.rss"),  # Expository
        ],
        "high_impact": [
            # Top research journals
            ("Annals of Mathematics", "https://annals.math.princeton.edu/feed/"),  # Top journal
            ("J. American Math Society", "https://www.ams.org/rss/jams.rss"),  # Top journal
            ("Inventiones Mathematicae", "https://link.springer.com/search.rss?facet-content-type=Article&facet-journal-id=222"),
            ("Acta Mathematica", "https://link.springer.com/search.rss?facet-content-type=Article&facet-journal-id=11511"),
        ],
        "education": [
            ("College Math Journal", "https://www.tandfonline.com/feed/rss/ucmj20"),
            ("American Math Monthly", "https://www.tandfonline.com/feed/rss/uamm20"),
        ]
    },

    "engineering": {
        "review": [
            # Review journals - perfect for Deep Dive
            ("Progress in Materials Sci", "https://rss.sciencedirect.com/publication/science/00796425"),  # IF 37
            ("Renewable & Sustainable Energy Rev", "https://rss.sciencedirect.com/publication/science/13640321"),  # IF 16
            ("Progress in Energy & Combustion", "https://rss.sciencedirect.com/publication/science/03601285"),  # IF 35
        ],
        "high_impact": [
            # Top research journals
            ("Nature Materials", "https://www.nature.com/nmat.rss"),  # IF 41
            ("Nature Energy", "https://www.nature.com/nenergy.rss"),  # IF 67
            ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),  # News + features
            ("Joule", "https://www.cell.com/joule/rss"),  # IF 46
        ],
        "education": [
            ("J. Engineering Education", "https://onlinelibrary.wiley.com/feed/21689830/most-recent"),
        ]
    },

    "agriculture": {
        "review": [
            # Review journals - perfect for Deep Dive
            ("Trends in Plant Science", "https://www.cell.com/trends/plant-science/rss"),  # IF 20
            ("Annual Rev Plant Biology", "https://www.annualreviews.org/rss/content/journals/arplant?fmt=rss"),  # IF 22
            ("Nature Plants", "https://www.nature.com/nplants.rss"),  # IF 18 (has reviews)
        ],
        "high_impact": [
            # Top research journals
            ("Nature Food", "https://www.nature.com/natfood.rss"),  # IF 24
            ("Plant Cell", "https://academic.oup.com/rss/site_5326/3172.xml"),  # IF 12
            ("Global Food Security", "https://rss.sciencedirect.com/publication/science/22119124"),  # IF 7
            ("Food Chemistry", "https://rss.sciencedirect.com/publication/science/03088146"),  # IF 9
        ],
        "education": [
            ("J. Agricultural Education", "https://www.jae-online.org/index.php/jae/gateway/plugin/WebFeedGatewayPlugin/rss2"),
        ]
    },

    "ai": {
        "review": [
            # Review journals - perfect for Deep Dive
            ("arXiv cs.LG", "https://rss.arxiv.org/rss/cs.LG"),  # FREE PDFs! Machine Learning
            ("arXiv cs.AI", "https://rss.arxiv.org/rss/cs.AI"),  # FREE PDFs! AI
            ("ACM Computing Surveys", "https://dl.acm.org/action/showFeed?type=etoc&feed=rss&jc=csur"),  # IF 16
            ("AI Magazine", "https://ojs.aaai.org/index.php/aimagazine/gateway/plugin/WebFeedGatewayPlugin/atom"),
        ],
        "high_impact": [
            # Top research venues
            ("Nature Machine Intelligence", "https://www.nature.com/natmachintell.rss"),  # IF 25
            ("JMLR", "https://jmlr.org/jmlr.xml"),  # Top ML journal, OPEN ACCESS
        ],
        "education": [
            ("ACM SIGCSE", "https://dl.acm.org/action/showFeed?type=etoc&feed=rss&jc=sigcse"),
        ]
    }
}


def init_db():
    """Initialize the articles database"""
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS seen_articles (
            url TEXT PRIMARY KEY,
            headline TEXT,
            discipline TEXT,
            source_type TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            headline TEXT,
            teaser TEXT,
            source TEXT,
            discipline TEXT,
            article_type TEXT,
            week TEXT,
            approved_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn


def is_article_seen(conn, url):
    """Check if article URL has been seen before"""
    cur = conn.execute("SELECT 1 FROM seen_articles WHERE url = ?", (url,))
    return cur.fetchone() is not None


def mark_article_seen(conn, url, headline, discipline, source_type):
    """Mark an article as seen"""
    conn.execute(
        "INSERT OR IGNORE INTO seen_articles (url, headline, discipline, source_type) VALUES (?, ?, ?, ?)",
        (url, headline, discipline, source_type)
    )
    conn.commit()


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_feed(feed_url, source_name, discipline, source_type, conn):
    """Fetch and parse a single feed"""
    articles = []
    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            print(f"    - {source_name}: error parsing")
            return articles

        for entry in feed.entries[:10]:  # Limit per feed
            url = entry.get('link', '')
            if not url or is_article_seen(conn, url):
                continue

            headline = clean_text(entry.get('title', ''))
            if not headline:
                continue

            # Get teaser/summary
            teaser = ""
            if 'summary' in entry:
                teaser = clean_text(entry.summary)[:500]
            elif 'description' in entry:
                teaser = clean_text(entry.description)[:500]

            # Extract DOI if available
            doi = ""
            if "doi.org" in url:
                doi = url.split("doi.org/")[-1]
            elif "dx.doi.org" in url:
                doi = url.split("dx.doi.org/")[-1]
            elif entry.get('id', '').startswith('10.'):
                doi = entry.get('id')

            # Check if Open Access
            is_open_access = any(oa in source_name for oa in OPEN_ACCESS_SOURCES)

            articles.append({
                "headline": headline,
                "teaser": teaser,
                "url": url,
                "doi": doi,
                "source": source_name,
                "source_type": source_type,
                "discipline": discipline,
                "deep_dive_candidate": source_type == "review",
                "open_access": is_open_access,
                "pdf_link": f"https://sci-hub.se/{doi}" if doi else ""  # For reference
            })

            mark_article_seen(conn, url, headline, discipline, source_type)

        if articles:
            print(f"    + {source_name}: {len(articles)} new")
        else:
            print(f"    - {source_name}: 0 new")

    except Exception as e:
        print(f"    x {source_name}: {str(e)[:50]}")

    return articles


def collect_all():
    """Collect articles from all curated feeds"""
    print(f"\n{'='*60}")
    print(f"The Beakers Feed Collector v2")
    print(f"Curated Collection - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    conn = init_db()
    all_articles = {}

    for discipline, sources in FEEDS.items():
        print(f"\n{'='*40}")
        print(f"  {discipline.upper()}")
        print(f"{'='*40}")

        all_articles[discipline] = {
            "review": [],      # Deep Dive candidates
            "high_impact": [], # Regular summaries
            "education": []    # Teaching resources
        }

        # Collect from REVIEW journals (Deep Dive candidates)
        print("  REVIEW (Deep Dive candidates):")
        for source_name, feed_url in sources.get("review", []):
            articles = fetch_feed(feed_url, source_name, discipline, "review", conn)
            all_articles[discipline]["review"].extend(articles)

        # Collect from HIGH IMPACT journals (Regular summaries)
        print("  HIGH IMPACT (Regular summaries):")
        for source_name, feed_url in sources.get("high_impact", []):
            articles = fetch_feed(feed_url, source_name, discipline, "high_impact", conn)
            all_articles[discipline]["high_impact"].extend(articles)

        # Collect from EDUCATION journals
        print("  EDUCATION:")
        for source_name, feed_url in sources.get("education", []):
            articles = fetch_feed(feed_url, source_name, discipline, "education", conn)
            all_articles[discipline]["education"].extend(articles)

    conn.close()

    # Save to pending_articles.json
    output = {
        "collected": datetime.now().isoformat(),
        "week": datetime.now().strftime("%Y-W%W"),
        "version": 2,
        "disciplines": all_articles
    }

    output_path = DATA_DIR / "pending_articles.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"{'Discipline':<15} {'Review':<10} {'High-Impact':<12} {'Education':<10}")
    print("-" * 50)

    total_review = 0
    total_high = 0
    total_edu = 0

    for discipline, sources in all_articles.items():
        r = len(sources["review"])
        h = len(sources["high_impact"])
        e = len(sources["education"])
        total_review += r
        total_high += h
        total_edu += e
        print(f"{discipline:<15} {r:<10} {h:<12} {e:<10}")

    print("-" * 50)
    print(f"{'TOTAL':<15} {total_review:<10} {total_high:<12} {total_edu:<10}")
    print(f"\nDeep Dive candidates: {total_review}")
    print(f"Regular candidates: {total_high}")
    print(f"\nSaved to: {output_path}")

    return all_articles


def show_deep_dive_candidates():
    """Show review articles available for Deep Dive"""
    pending_path = DATA_DIR / "pending_articles.json"
    if not pending_path.exists():
        print("Run collector first: python feed_collector.py")
        return

    with open(pending_path) as f:
        data = json.load(f)

    print(f"\n{'='*70}")
    print("DEEP DIVE CANDIDATES (Review Articles)")
    print("For NotebookLM: Download PDF, upload to notebook, generate content")
    print(f"{'='*70}")

    for discipline, sources in data.get("disciplines", {}).items():
        reviews = sources.get("review", [])
        if reviews:
            print(f"\n{'='*50}")
            print(f"{discipline.upper()}")
            print(f"{'='*50}")
            for i, article in enumerate(reviews[:5], 1):
                oa_badge = "[OPEN ACCESS]" if article.get('open_access') else ""
                print(f"\n  {i}. {article['headline'][:65]}...")
                print(f"     Source: {article['source']} {oa_badge}")
                if article.get('doi'):
                    print(f"     DOI: {article['doi']}")
                    print(f"     PDF: https://doi.org/{article['doi']}")
                else:
                    print(f"     URL: {article['url']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "deepdive":
        show_deep_dive_candidates()
    else:
        collect_all()
        print("\nRun 'python feed_collector.py deepdive' to see Deep Dive candidates")
