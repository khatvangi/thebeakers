#!/usr/bin/env python3
"""
The Beakers Feed Collector v3
Curated journal RSS + lead generators (HN/Reddit/News) feeding the same discriminator.

Goals:
- keep your existing v2 behavior
- add lead sources WITHOUT turning the site into hype/clickbait
- produce one pending file: data/pending_articles.json
- add a scoring + hype-penalty layer so you can curate fast

Notes:
- Reddit: uses subreddit RSS feeds (no API keys; avoids scraping gray zones)
- Hacker News: uses official Firebase API (JSON endpoints)
- News outlets: RSS only (no scraping paywalled pages)
"""

import feedparser
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import html
import socket
import urllib.request
import urllib.error

# -----------------------------------------------------------------------------
# networking
# -----------------------------------------------------------------------------
socket.setdefaulttimeout(15)

def http_get_json(url: str, timeout: int = 15):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "thebeakers/1.0 (https://thebeakers.com)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8", errors="replace")
        return json.loads(data)

# -----------------------------------------------------------------------------
# paths
# -----------------------------------------------------------------------------
BEAKERS_DIR = Path(__file__).parent.parent
DATA_DIR = BEAKERS_DIR / "data"
DB_PATH = DATA_DIR / "articles.db"

# -----------------------------------------------------------------------------
# curation + scoring
# -----------------------------------------------------------------------------
CLICKBAIT_PATTERNS = [
    r"\bshocking\b", r"\bstuns\b", r"\bblows?\b", r"\bgame[- ]changer\b",
    r"\bchanges? everything\b", r"\byou won'?t believe\b", r"\bsecret\b",
    r"\binstantly\b", r"\bovernight\b", r"\bmiracle\b", r"\bbreaking\b",
    r"\bwhat happens next\b", r"\bthe truth\b", r"\bworld[- ]first\b",
    r"\bdoctors hate\b", r"\bthis one trick\b", r"!{1,}",
]
CLICKBAIT_RE = re.compile("|".join(CLICKBAIT_PATTERNS), re.IGNORECASE)

# Lightweight keyword routing for lead sources (HN, general news, etc.)
DISCIPLINE_KEYWORDS = {
    "chemistry": [
        "chem", "catal", "polymer", "electrolyte", "battery", "solar cell", "photovolta",
        "synthesis", "reaction", "spectroscopy", "nmr", "electrochem", "materials chemistry"
    ],
    "physics": [
        "quantum", "particle", "condensed", "superconduct", "graphene", "fusion", "plasma",
        "astroph", "cosmolog", "optics", "photon", "relativity"
    ],
    "biology": [
        "genome", "protein", "cell", "crispr", "immun", "microbi", "evolution", "neuro",
        "cancer", "metabol", "rna", "virus", "pathogen"
    ],
    "engineering": [
        "robot", "control", "mechanical", "electrical", "sensor", "chip", "semiconductor",
        "signal", "power", "thermal", "manufactur", "civil", "aerospace"
    ],
    "mathematics": [
        "theorem", "proof", "algebra", "geometry", "topology", "number theory", "optimization",
        "differential", "probability", "statistics"
    ],
    "ai": [
        "machine learning", "deep learning", "neural", "transformer", "llm", "diffusion",
        "reinforcement", "computer vision", "nlp", "foundation model"
    ],
    "agriculture": [
        "crop", "soil", "plant", "agric", "farm", "irrig", "fertil", "nitrogen", "pest",
        "drought", "yield", "livestock", "food security"
    ],
}

def guess_discipline(title: str, fallback: str = "biology") -> str:
    t = (title or "").lower()
    scores = {k: 0 for k in DISCIPLINE_KEYWORDS}
    for d, kws in DISCIPLINE_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                scores[d] += 1
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else fallback

def hype_penalty(headline: str) -> float:
    if not headline:
        return 0.0
    h = headline.strip()
    penalty = 0.0
    if CLICKBAIT_RE.search(h):
        penalty += 2.0
    if sum(1 for c in h if c.isupper()) >= 12:  # lots of caps
        penalty += 1.0
    if len(h) > 120:
        penalty += 0.5
    return penalty

def recency_bonus(published_dt) -> float:
    if not published_dt:
        return 0.0
    now = datetime.now(timezone.utc)
    try:
        days = (now - published_dt).days
    except Exception:
        return 0.0
    if days <= 2:
        return 1.0
    if days <= 7:
        return 0.6
    if days <= 21:
        return 0.2
    return 0.0

def score_article(a: dict) -> float:
    """
    Opinionated, research-first scoring:
    - prefer peer-reviewed journals (your existing FEEDS) over leads
    - reward DOI presence and open-access hints
    - penalize hype
    """
    base = 0.0

    source_type = a.get("source_type", "")
    origin = a.get("origin", "journal")  # journal | lead

    if origin == "journal":
        if source_type == "review":
            base += 6.0
        elif source_type == "education":
            base += 5.0
        elif source_type == "high_impact":
            base += 4.0
        else:
            base += 3.0
    else:
        # leads are lead generators, not final authority
        base += 2.0

    if a.get("doi"):
        base += 2.0

    if a.get("open_access"):
        base += 1.0

    base += recency_bonus(a.get("published_dt"))

    base -= hype_penalty(a.get("headline", ""))

    # small reward if we see "PDF" link hints (some RSS include them)
    if a.get("pdf_url"):
        base += 0.7

    return round(base, 3)

# -----------------------------------------------------------------------------
# feeds (your existing curated set + minimal additions)
# -----------------------------------------------------------------------------
OPEN_ACCESS_SOURCES = {
    "eLife", "PLOS", "Nature Communications", "Scientific Reports",
    "MDPI", "Frontiers", "PeerJ", "BMC", "JMLR",
    "J. Chem. Education", "American J. Physics", "The Physics Teacher",
    "CBE Life Sci Education", "J. Engineering Education"
}

FEEDS = {
    "chemistry": {
        "review": [
            ("Chemical Reviews", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=chreay"),
            ("Chem Society Reviews", "https://pubs.rsc.org/en/journals/journalissues/cs?_type=rss"),
            ("Acc. Chemical Research", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=achre4"),
        ],
        "high_impact": [
            ("JACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jacsat"),
            ("Nature Chemistry", "https://www.nature.com/nchem.rss"),
            ("Angewandte Chemie", "https://onlinelibrary.wiley.com/feed/15213773/most-recent"),
            ("ACS Central Science", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=acscii"),
        ],
        "education": [
            ("J. Chem. Education", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jceda8"),
        ]
    },
    "physics": {
        "review": [
            ("Reviews of Modern Physics", "https://feeds.aps.org/rss/recent/rmp.xml"),
            ("Physics Reports", "https://rss.sciencedirect.com/publication/science/03701573"),
            ("Reports on Progress in Physics", "https://iopscience.iop.org/journal/rss/0034-4885"),
        ],
        "high_impact": [
            ("Nature Physics", "https://www.nature.com/nphys.rss"),
            ("Physical Review Letters", "https://feeds.aps.org/rss/recent/prl.xml"),
            ("Physical Review X", "https://feeds.aps.org/rss/recent/prx.xml"),
        ],
        "education": [
            ("American J. Physics", "https://pubs.aip.org/rss/site_1000029/1000029.xml"),
            ("The Physics Teacher", "https://pubs.aip.org/rss/site_1000031/1000031.xml"),
        ]
    },
    "biology": {
        "review": [
            ("eLife", "https://elifesciences.org/rss/recent.xml"),
            ("Nature Rev Genetics", "https://www.nature.com/nrg.rss"),
            ("Nature Rev Mol Cell Bio", "https://www.nature.com/nrm.rss"),
            ("Annual Rev Biochemistry", "https://www.annualreviews.org/rss/content/journals/biochem?fmt=rss"),
            ("Trends in Biochem Sci", "https://www.cell.com/trends/biochemical-sciences/rss"),
        ],
        "high_impact": [
            ("Nature", "https://www.nature.com/nature.rss"),
            ("Cell", "https://www.cell.com/cell/rss"),
            ("Science", "https://www.science.org/rss/news_current.xml"),
        ],
        "education": [
            ("CBE Life Sci Education", "https://www.lifescied.org/rss/recent.xml"),
        ]
    },
    "mathematics": {
        "review": [
            ("SIAM Review", "https://epubs.siam.org/action/showFeed?type=etoc&feed=rss&jc=siread"),
            ("Bulletin of the AMS", "https://www.ams.org/rss/bull.rss"),
            ("Notices of the AMS", "https://www.ams.org/rss/notices.rss"),
        ],
        "high_impact": [
            ("Annals of Mathematics", "https://annals.math.princeton.edu/feed/"),
            ("J. American Math Society", "https://www.ams.org/rss/jams.rss"),
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
            ("Progress in Materials Sci", "https://rss.sciencedirect.com/publication/science/00796425"),
            ("Renewable & Sustainable Energy Rev", "https://rss.sciencedirect.com/publication/science/13640321"),
            ("Progress in Energy & Combustion", "https://rss.sciencedirect.com/publication/science/03601285"),
        ],
        "high_impact": [
            ("Nature Materials", "https://www.nature.com/nmat.rss"),
            ("Nature Energy", "https://www.nature.com/nenergy.rss"),
            ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
            ("Joule", "https://www.cell.com/joule/rss"),
        ],
        "education": [
            ("J. Engineering Education", "https://onlinelibrary.wiley.com/feed/21689830/most-recent"),
        ]
    },
    "agriculture": {
        "review": [
            ("Trends in Plant Science", "https://www.cell.com/trends/plant-science/rss"),
            ("Annual Rev Plant Biology", "https://www.annualreviews.org/rss/content/journals/arplant?fmt=rss"),
            ("Nature Plants", "https://www.nature.com/nplants.rss"),
        ],
        "high_impact": [
            ("Nature Food", "https://www.nature.com/natfood.rss"),
            ("Plant Cell", "https://academic.oup.com/rss/site_5326/3172.xml"),
            ("Global Food Security", "https://rss.sciencedirect.com/publication/science/22119124"),
            ("Food Chemistry", "https://rss.sciencedirect.com/publication/science/03088146"),
        ],
        "education": [
            ("J. Agricultural Education", "https://www.jae-online.org/index.php/jae/gateway/plugin/WebFeedGatewayPlugin/rss2"),
        ]
    },
    "ai": {
        "review": [
            ("ACM Computing Surveys", "https://dl.acm.org/action/showFeed?type=etoc&feed=rss&jc=csur"),
            ("AI Magazine", "https://ojs.aaai.org/index.php/aimagazine/gateway/plugin/WebFeedGatewayPlugin/atom"),
            ("JMLR", "https://jmlr.org/jmlr.xml"),
        ],
        "high_impact": [
            ("Nature Machine Intelligence", "https://www.nature.com/natmachintell.rss"),
        ],
        "education": [
            ("ACM SIGCSE", "https://dl.acm.org/action/showFeed?type=etoc&feed=rss&jc=sigcse"),
            ("Computer Science Education", "https://www.tandfonline.com/feed/rss/ncse20"),
        ]
    }
}

# -----------------------------------------------------------------------------
# lead generators (additive, not replacing journals)
# -----------------------------------------------------------------------------
LEAD_RSS = {
    # discipline -> list of (source, rss_url)
    "chemistry": [
        # C&EN latest news (feedburner)
        ("C&EN Latest News", "http://feeds.feedburner.com/cen_latestnews"),
        # ACS Axial (generally accessible)
        ("ACS Axial", "https://www.acs.org/axial/rss.xml"),
    ],
    "biology": [
        ("MIT News - Research", "https://news.mit.edu/rss/topic/research"),
        ("Nature (journal) RSS", "https://www.nature.com/nature.rss"),
        ("Science - News", "https://www.science.org/rss/news_current.xml"),
    ],
    "physics": [
        ("MIT News - School of Science", "https://news.mit.edu/rss/topic/school-science"),
        ("Science - News", "https://www.science.org/rss/news_current.xml"),
        ("Nature (journal) RSS", "https://www.nature.com/nature.rss"),
    ],
    "engineering": [
        ("MIT News - School of Engineering", "https://news.mit.edu/rss/topic/school-engineering"),
        ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
    ],
    "agriculture": [
        # keep sparse: let journals dominate; add one broad science feed as lead
        ("Science - News", "https://www.science.org/rss/news_current.xml"),
        ("Nature (journal) RSS", "https://www.nature.com/nature.rss"),
    ],
    "mathematics": [
        ("MIT News - School of Science", "https://news.mit.edu/rss/topic/school-science"),
    ],
    "ai": [
        ("MIT News - Artificial intelligence", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
        ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
    ]
}

REDDIT_SUBS = {
    "chemistry": ["chemistry", "OrganicChemistry", "computationalchemistry", "MaterialsScience"],
    "biology": ["biology", "genetics", "microbiology", "bioinformatics", "neuroscience"],
    "physics": ["Physics", "Quantum", "CondensedMatter", "astrophysics"],
    "engineering": ["engineering", "robotics", "ControlTheory", "ElectricalEngineering", "MechanicalEngineering"],
    "agriculture": ["Agriculture", "plantbiology", "soil", "Permaculture", "AgTech"],
    "mathematics": ["math", "mathresearch", "statistics"],
    "ai": ["MachineLearning", "artificial", "deeplearning", "LocalLLaMA"],
}

def reddit_rss_url(sub: str) -> str:
    # RSS endpoint: https://www.reddit.com/r/{sub}/.rss
    return f"https://www.reddit.com/r/{sub}/.rss"

HN_ENDPOINTS = {
    "top": "https://hacker-news.firebaseio.com/v0/topstories.json",
    "best": "https://hacker-news.firebaseio.com/v0/beststories.json",
}
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"

# -----------------------------------------------------------------------------
# db
# -----------------------------------------------------------------------------
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
    cur = conn.execute("SELECT 1 FROM seen_articles WHERE url = ?", (url,))
    return cur.fetchone() is not None

def mark_article_seen(conn, url, headline, discipline, source_type):
    conn.execute(
        "INSERT OR IGNORE INTO seen_articles (url, headline, discipline, source_type) VALUES (?, ?, ?, ?)",
        (url, headline, discipline, source_type)
    )
    conn.commit()

# -----------------------------------------------------------------------------
# parsing helpers
# -----------------------------------------------------------------------------
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)

def clean_text(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_doi(text: str) -> str:
    if not text:
        return ""
    m = DOI_RE.search(text)
    return m.group(0) if m else ""

def extract_pdf_url(entry) -> str:
    # conservative: only if rss gives explicit pdf link
    links = entry.get("links", []) or []
    for l in links:
        href = l.get("href", "")
        if href and (href.lower().endswith(".pdf") or "pdf" in (l.get("type", "") or "").lower()):
            return href
    return ""

def parse_published_dt(entry):
    # feedparser provides published_parsed / updated_parsed as time.struct_time
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if not t:
        return None
    try:
        return datetime(*t[:6], tzinfo=timezone.utc)
    except Exception:
        return None

# -----------------------------------------------------------------------------
# core collectors
# -----------------------------------------------------------------------------
def fetch_feed(feed_url, source_name, discipline, source_type, conn, origin="journal"):
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo and not feed.entries:
            print(f"    - {source_name}: error parsing")
            return articles

        for entry in feed.entries[:12]:
            url = entry.get('link', '')
            if not url or is_article_seen(conn, url):
                continue

            headline = clean_text(entry.get('title', ''))
            if not headline:
                continue

            teaser = ""
            if 'summary' in entry:
                teaser = clean_text(entry.summary)[:700]
            elif 'description' in entry:
                teaser = clean_text(entry.description)[:700]

            published_dt = parse_published_dt(entry)

            # DOI extraction: check url + entry id + teaser
            doi = ""
            if "doi.org" in url:
                doi = url.split("doi.org/")[-1]
            elif "dx.doi.org" in url:
                doi = url.split("dx.doi.org/")[-1]
            elif entry.get('id', '').startswith('10.'):
                doi = entry.get('id')
            else:
                doi = extract_doi(" ".join([url, entry.get("id", ""), teaser, headline]))

            # OA heuristic: based on the source name bucket, not article-level truth
            is_open_access = any(oa in source_name for oa in OPEN_ACCESS_SOURCES)

            is_deep_dive = source_type in ("review", "education")

            pdf_url = extract_pdf_url(entry)

            a = {
                "headline": headline,
                "teaser": teaser,
                "url": url,
                "doi": doi,
                "pdf_url": pdf_url,
                "source": source_name,
                "source_type": source_type,
                "discipline": discipline,
                "deep_dive_candidate": is_deep_dive,
                "open_access": is_open_access,
                "origin": origin,
                "published_dt": published_dt.isoformat() if published_dt else ""
            }
            a["score"] = score_article({**a, "published_dt": published_dt})

            articles.append(a)
            mark_article_seen(conn, url, headline, discipline, source_type)

        if articles:
            print(f"    + {source_name}: {len(articles)} new")
        else:
            print(f"    - {source_name}: 0 new")

    except Exception as e:
        print(f"    x {source_name}: {str(e)[:80]}")

    return articles

def collect_hackernews(conn, limit=60):
    """
    Pull HN top+best, classify by keywords, return list of lead items.
    Only collects external URLs (skip 'Ask HN' etc).
    """
    out = []
    try:
        ids = []
        for name, endpoint in HN_ENDPOINTS.items():
            data = http_get_json(endpoint)
            ids.extend(data[: limit // 2])

        seen = set()
        for story_id in ids:
            if story_id in seen:
                continue
            seen.add(story_id)

            item = http_get_json(HN_ITEM.format(id=story_id))
            if not item:
                continue

            url = item.get("url", "")
            title = item.get("title", "") or ""
            if not url or not title:
                continue

            # skip internal HN discussions (no external URL)
            if url.startswith("item?") or "news.ycombinator.com" in url:
                continue

            discipline = guess_discipline(title, fallback="ai")

            if is_article_seen(conn, url):
                continue

            published_dt = None
            ts = item.get("time")
            if ts:
                try:
                    published_dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                except Exception:
                    published_dt = None

            teaser = f"HN score {item.get('score', 0)}, comments {item.get('descendants', 0)}"

            a = {
                "headline": clean_text(title),
                "teaser": teaser,
                "url": url,
                "doi": extract_doi(url + " " + title),
                "pdf_url": "",
                "source": "Hacker News",
                "source_type": "lead_hn",
                "discipline": discipline,
                "deep_dive_candidate": False,
                "open_access": False,
                "origin": "lead",
                "published_dt": published_dt.isoformat() if published_dt else ""
            }
            a["score"] = score_article({**a, "published_dt": published_dt})

            out.append(a)
            mark_article_seen(conn, url, a["headline"], discipline, "lead_hn")

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"    x Hacker News: {str(e)[:80]}")
    except Exception as e:
        print(f"    x Hacker News: {str(e)[:80]}")

    return out

def collect_reddit(conn, discipline: str, subs: list[str], per_sub=10):
    out = []
    for sub in subs:
        src = f"Reddit r/{sub}"
        rss = reddit_rss_url(sub)
        try:
            feed = feedparser.parse(rss)
            if feed.bozo and not feed.entries:
                continue

            for entry in feed.entries[:per_sub]:
                url = entry.get("link", "")
                headline = clean_text(entry.get("title", ""))
                if not url or not headline:
                    continue
                if is_article_seen(conn, url):
                    continue

                teaser = clean_text(entry.get("summary", ""))[:700]
                doi = extract_doi(" ".join([url, headline, teaser]))
                published_dt = parse_published_dt(entry)
                pdf_url = extract_pdf_url(entry)

                a = {
                    "headline": headline,
                    "teaser": teaser,
                    "url": url,
                    "doi": doi,
                    "pdf_url": pdf_url,
                    "source": src,
                    "source_type": "lead_reddit",
                    "discipline": discipline,
                    "deep_dive_candidate": False,
                    "open_access": False,
                    "origin": "lead",
                    "published_dt": published_dt.isoformat() if published_dt else ""
                }
                a["score"] = score_article({**a, "published_dt": published_dt})

                out.append(a)
                mark_article_seen(conn, url, headline, discipline, "lead_reddit")

        except Exception:
            continue
    return out

# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
def collect_all():
    print(f"\n{'='*60}")
    print("The Beakers Feed Collector v3")
    print(f"Curated Journals + Lead Generators - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    conn = init_db()

    all_articles = {}
    leads = {
        "hackernews": [],
        "reddit": {},
        "news_rss": {}
    }

    # 1) core: curated journals
    for discipline, sources in FEEDS.items():
        print(f"\n{'='*40}")
        print(f"  {discipline.upper()}")
        print(f"{'='*40}")

        all_articles[discipline] = {"review": [], "high_impact": [], "education": []}

        print("  REVIEW (Deep Dive candidates):")
        for source_name, feed_url in sources.get("review", []):
            all_articles[discipline]["review"].extend(
                fetch_feed(feed_url, source_name, discipline, "review", conn, origin="journal")
            )

        print("  HIGH IMPACT (Regular summaries):")
        for source_name, feed_url in sources.get("high_impact", []):
            all_articles[discipline]["high_impact"].extend(
                fetch_feed(feed_url, source_name, discipline, "high_impact", conn, origin="journal")
            )

        print("  EDUCATION:")
        for source_name, feed_url in sources.get("education", []):
            all_articles[discipline]["education"].extend(
                fetch_feed(feed_url, source_name, discipline, "education", conn, origin="journal")
            )

        # keep each bucket sorted by score descending
        for k in all_articles[discipline]:
            all_articles[discipline][k].sort(key=lambda x: x.get("score", 0), reverse=True)

    # 2) leads: Hacker News (global)
    print(f"\n{'='*40}")
    print("  LEADS: HACKER NEWS")
    print(f"{'='*40}")
    hn_items = collect_hackernews(conn, limit=70)
    hn_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    print(f"    + Hacker News: {len(hn_items)} new")
    leads["hackernews"] = hn_items[:50]  # cap output

    # 3) leads: Reddit per discipline
    print(f"\n{'='*40}")
    print("  LEADS: REDDIT (subreddit RSS)")
    print(f"{'='*40}")
    for discipline, subs in REDDIT_SUBS.items():
        items = collect_reddit(conn, discipline, subs, per_sub=8)
        items.sort(key=lambda x: x.get("score", 0), reverse=True)
        leads["reddit"][discipline] = items[:35]
        print(f"    + {discipline}: {len(items)} new")

    # 4) leads: high-quality news RSS per discipline (C&EN, MIT, Science, Nature, IEEE)
    print(f"\n{'='*40}")
    print("  LEADS: NEWS RSS (high-quality outlets)")
    print(f"{'='*40}")
    for discipline, feeds in LEAD_RSS.items():
        leads["news_rss"][discipline] = []
        for source_name, rss_url in feeds:
            leads["news_rss"][discipline].extend(
                fetch_feed(rss_url, source_name, discipline, "lead_news", conn, origin="lead")
            )
        leads["news_rss"][discipline].sort(key=lambda x: x.get("score", 0), reverse=True)
        print(f"    + {discipline}: {len(leads['news_rss'][discipline])} new")

    conn.close()

    # single output artifact, compatible with your current pipeline
    output = {
        "collected": datetime.now().isoformat(),
        "week": datetime.now().strftime("%Y-W%W"),
        "version": 3,
        "disciplines": all_articles,
        "leads": leads,
        "scoring": {
            "notes": [
                "journals outrank leads by default",
                "DOI and recency increase score",
                "clickbait patterns and excess caps decrease score",
                "leads are for discovery; journals are for authority"
            ]
        }
    }

    output_path = DATA_DIR / "pending_articles.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    # summary
    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"{'Discipline':<15} {'Review':<10} {'High-Impact':<12} {'Education':<10} {'Leads':<8}")
    print("-" * 62)

    total_review = total_high = total_edu = total_leads = 0
    for discipline, sources in all_articles.items():
        r = len(sources["review"])
        h = len(sources["high_impact"])
        e = len(sources["education"])
        l = len(leads["reddit"].get(discipline, [])) + len(leads["news_rss"].get(discipline, []))
        total_review += r
        total_high += h
        total_edu += e
        total_leads += l
        print(f"{discipline:<15} {r:<10} {h:<12} {e:<10} {l:<8}")

    print("-" * 62)
    print(f"{'TOTAL':<15} {total_review:<10} {total_high:<12} {total_edu:<10} {total_leads:<8}")
    print(f"\nHN leads: {len(leads['hackernews'])}")
    print(f"\nSaved to: {output_path}")

    return output

def show_deep_dive_candidates():
    pending_path = DATA_DIR / "pending_articles.json"
    if not pending_path.exists():
        print("Run collector first: python feed_collector.py")
        return

    with open(pending_path) as f:
        data = json.load(f)

    print(f"\n{'='*70}")
    print("DEEP DIVE CANDIDATES (JOURNALS ONLY)")
    print("Review articles + Education articles = best NotebookLM candidates")
    print(f"{'='*70}")

    for discipline, sources in data.get("disciplines", {}).items():
        reviews = sources.get("review", [])
        education = sources.get("education", [])
        candidates = (reviews + education)
        candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

        if not candidates:
            continue

        print(f"\n{'='*50}")
        print(discipline.upper())
        print(f"{'='*50}")

        for i, a in enumerate(candidates[:6], 1):
            oa_badge = "[OA?]" if a.get("open_access") else ""
            doi = a.get("doi", "")
            score = a.get("score", 0)
            print(f"  {i}. ({score}) {a['headline'][:88]}")
            print(f"     {a['source']} {oa_badge}")
            if doi:
                print(f"     doi: https://doi.org/{doi}")

def show_lead_highlights():
    pending_path = DATA_DIR / "pending_articles.json"
    if not pending_path.exists():
        print("Run collector first: python feed_collector.py")
        return

    with open(pending_path) as f:
        data = json.load(f)

    leads = data.get("leads", {})
    hn = leads.get("hackernews", [])[:12]

    print(f"\n{'='*70}")
    print("LEAD HIGHLIGHTS (DISCOVERY ONLY — VERIFY BEFORE WRITING)")
    print(f"{'='*70}")

    if hn:
        print("\nHACKER NEWS:")
        for i, a in enumerate(hn, 1):
            print(f"  {i}. ({a.get('score',0)}) {a['headline'][:92]}")
            print(f"     {a['url']}")

    reddit = leads.get("reddit", {})
    news_rss = leads.get("news_rss", {})

    for discipline in sorted(set(list(reddit.keys()) + list(news_rss.keys()))):
        items = (reddit.get(discipline, [])[:6] + news_rss.get(discipline, [])[:6])
        items.sort(key=lambda x: x.get("score", 0), reverse=True)
        if not items:
            continue

        print(f"\n{discipline.upper()}:")
        for i, a in enumerate(items[:10], 1):
            print(f"  {i}. ({a.get('score',0)}) {a['headline'][:92]}")
            print(f"     {a['source']} | {a['url']}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "deepdive":
        show_deep_dive_candidates()
    elif len(sys.argv) > 1 and sys.argv[1] == "leads":
        show_lead_highlights()
    else:
        collect_all()
        print("\nCommands:")
        print("  python feed_collector.py deepdive   # best NotebookLM candidates (review+education)")
        print("  python feed_collector.py leads      # discovery feed (HN/Reddit/News) — verify before use")

