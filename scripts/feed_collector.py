#!/usr/bin/env python3
"""
The Beakers Feed Collector
Fetches articles from research + education journals
Weekly collection for STEM disciplines
"""

import feedparser
import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import html
import socket

# Set network timeout
socket.setdefaulttimeout(15)

# Paths
BEAKERS_DIR = Path(__file__).parent.parent
DATA_DIR = BEAKERS_DIR / "data"
DB_PATH = DATA_DIR / "articles.db"

# RSS Feeds organized by discipline
# Each has: research journals + education journals
FEEDS = {
    "chemistry": {
        "research": [
            ("ACS Publications", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jacsat"),  # JACS
            ("ACS Central Science", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=acscii"),
            ("RSC Advances", "https://pubs.rsc.org/en/journals/journalissues/ra?_type=rss"),
            ("Nature Chemistry", "https://www.nature.com/nchem.rss"),
            ("Angewandte Chemie", "https://onlinelibrary.wiley.com/feed/15213773/most-recent"),
        ],
        "education": [
            ("J. Chem. Education", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jceda8"),
            ("Chemistry Education R&P", "https://pubs.rsc.org/en/journals/journalissues/rp?_type=rss"),
            ("Education in Chemistry", "https://edu.rsc.org/rss"),
        ]
    },
    "physics": {
        "research": [
            ("Physical Review Letters", "https://feeds.aps.org/rss/recent/prl.xml"),
            ("Physical Review X", "https://feeds.aps.org/rss/recent/prx.xml"),
            ("Nature Physics", "https://www.nature.com/nphys.rss"),
            ("Physics Today", "https://pubs.aip.org/rss/site_1000043/1000043.xml"),
        ],
        "education": [
            ("American J. Physics", "https://pubs.aip.org/rss/site_1000029/1000029.xml"),
            ("The Physics Teacher", "https://pubs.aip.org/rss/site_1000031/1000031.xml"),
            ("Physics Education", "https://iopscience.iop.org/journal/rss/0031-9120"),
        ]
    },
    "biology": {
        "research": [
            ("Nature", "https://www.nature.com/nature.rss"),
            ("Cell", "https://www.cell.com/cell/rss"),
            ("PNAS", "https://www.pnas.org/rss/current.xml"),
            ("Science", "https://www.science.org/rss/news_current.xml"),
            ("eLife", "https://elifesciences.org/rss/recent.xml"),
        ],
        "education": [
            ("CBE Life Sci Education", "https://www.lifescied.org/rss/recent.xml"),
            ("J. Biological Education", "https://www.tandfonline.com/feed/rss/rjbe20"),
        ]
    },
    "mathematics": {
        "research": [
            ("Annals of Mathematics", "https://annals.math.princeton.edu/feed/"),
            ("J. American Math Society", "https://www.ams.org/rss/jams.rss"),
            ("Inventiones Mathematicae", "https://link.springer.com/search.rss?facet-content-type=Article&facet-journal-id=222"),
        ],
        "education": [
            ("College Math Journal", "https://www.tandfonline.com/feed/rss/ucmj20"),
            ("American Math Monthly", "https://www.tandfonline.com/feed/rss/uamm20"),
            ("PRIMUS", "https://www.tandfonline.com/feed/rss/upri20"),
            ("Math Teacher Learning & Teaching", "https://pubs.nctm.org/rss/mtlt.xml"),
        ]
    },
    "engineering": {
        "research": [
            ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
            ("ASME J. Mechanical Design", "https://asmedigitalcollection.asme.org/rss/site_1000054/1000054.xml"),
            ("J. Structural Engineering", "https://ascelibrary.org/action/showFeed?type=etoc&feed=rss&jc=jsendh"),
        ],
        "education": [
            ("J. Engineering Education", "https://onlinelibrary.wiley.com/feed/21689830/most-recent"),
            ("Advances in Eng. Education", "https://advances.asee.org/feed/"),
            ("European J. Eng. Education", "https://www.tandfonline.com/feed/rss/ceee20"),
        ]
    },
    "agriculture": {
        "research": [
            ("Agronomy Journal", "https://acsess.onlinelibrary.wiley.com/feed/14350645/most-recent"),
            ("J. Agricultural Science", "https://www.cambridge.org/core/rss/product/id/1CE0BFAB89CE573B461F4F5BAB2F29C6"),
            ("Agriculture, Ecosystems & Env", "https://rss.sciencedirect.com/publication/science/01678809"),
        ],
        "education": [
            ("J. Agricultural Education", "https://www.jae-online.org/index.php/jae/gateway/plugin/WebFeedGatewayPlugin/rss2"),
            ("NACTA Journal", "https://www.nactateachers.org/index.php/journal/feed"),
        ]
    },
    "ai": {
        "research": [
            ("Nature Machine Intelligence", "https://www.nature.com/natmachintell.rss"),
            ("AI Magazine", "https://ojs.aaai.org/index.php/aimagazine/gateway/plugin/WebFeedGatewayPlugin/atom"),
            ("J. Machine Learning Research", "https://jmlr.org/jmlr.xml"),
            ("arXiv cs.AI", "https://rss.arxiv.org/rss/cs.AI"),
        ],
        "education": [
            ("ACM SIGCSE", "https://dl.acm.org/action/showFeed?type=etoc&feed=rss&jc=sigcse"),
            ("Computer Science Education", "https://www.tandfonline.com/feed/rss/ncse20"),
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

def extract_source(feed_url, entry):
    """Extract source name from feed URL or entry"""
    for discipline, sources in FEEDS.items():
        for source_type in ['research', 'education']:
            for name, url in sources.get(source_type, []):
                if url in feed_url or feed_url in url:
                    return name
    return "Unknown"

def fetch_feed(feed_url, source_name, discipline, source_type, conn):
    """Fetch and parse a single feed"""
    articles = []
    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            print(f"  ⚠ Error parsing {source_name}")
            return articles

        for entry in feed.entries[:15]:  # Limit per feed
            url = entry.get('link', '')
            if not url or is_article_seen(conn, url):
                continue

            headline = clean_text(entry.get('title', ''))
            if not headline:
                continue

            # Get teaser/summary
            teaser = ""
            if 'summary' in entry:
                teaser = clean_text(entry.summary)[:300]
            elif 'description' in entry:
                teaser = clean_text(entry.description)[:300]

            articles.append({
                "headline": headline,
                "teaser": teaser,
                "url": url,
                "source": source_name,
                "source_type": source_type,  # 'research' or 'education'
                "discipline": discipline
            })

            mark_article_seen(conn, url, headline, discipline, source_type)

        print(f"  ✓ {source_name}: {len(articles)} new articles")

    except Exception as e:
        print(f"  ✗ {source_name}: {e}")

    return articles

def collect_all():
    """Collect articles from all feeds"""
    print(f"\n{'='*60}")
    print(f"The Beakers Feed Collector - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    conn = init_db()
    all_articles = {}

    for discipline, sources in FEEDS.items():
        print(f"\n📚 {discipline.upper()}")
        all_articles[discipline] = {
            "research": [],
            "education": []
        }

        # Collect from research journals
        print("  Research journals:")
        for source_name, feed_url in sources.get("research", []):
            articles = fetch_feed(feed_url, source_name, discipline, "research", conn)
            all_articles[discipline]["research"].extend(articles)

        # Collect from education journals
        print("  Education journals:")
        for source_name, feed_url in sources.get("education", []):
            articles = fetch_feed(feed_url, source_name, discipline, "education", conn)
            all_articles[discipline]["education"].extend(articles)

    conn.close()

    # Save to pending_articles.json
    output = {
        "collected": datetime.now().isoformat(),
        "week": datetime.now().strftime("%Y-W%W"),
        "disciplines": all_articles
    }

    output_path = DATA_DIR / "pending_articles.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for discipline, sources in all_articles.items():
        research_count = len(sources["research"])
        education_count = len(sources["education"])
        print(f"  {discipline}: {research_count} research + {education_count} education")

    total = sum(len(s["research"]) + len(s["education"]) for s in all_articles.values())
    print(f"\n  TOTAL: {total} articles")
    print(f"  Saved to: {output_path}")

    return all_articles

if __name__ == "__main__":
    collect_all()
