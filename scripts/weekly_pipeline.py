#!/usr/bin/env python3
"""
The Beakers Weekly Pipeline
Automated: Collect → Score → Route → Generate → Publish

No Telegram needed - rubric handles curation.
"""

import os
import sys
import json
import sqlite3
import requests
import hashlib
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from pathlib import Path

# Paths
ROOT = Path("/storage/thebeakers")
NAPKIN = Path("/storage/napkin")
DATA_DIR = ROOT / "data"
CONTENT_DIR = ROOT / "content"
ISSUES_DIR = CONTENT_DIR / "issues"
NOTES_DIR = CONTENT_DIR / "notes"
DEEPDIVE_DIR = ROOT / "deepdive"
PDF_DIR = DATA_DIR / "pdfs"
DEEP_DIR = DATA_DIR / "deep"  # Deep candidates organized by subject

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# OpenAlex
OPENALEX_EMAIL = "thebeakerscom@gmail.com"

# Subjects and their OpenAlex concept IDs
SUBJECTS = {
    "chemistry": ["chemistry", "organic chemistry", "physical chemistry"],
    "physics": ["physics", "quantum mechanics", "condensed matter physics"],
    "biology": ["biology", "molecular biology", "cell biology"],
    "mathematics": ["mathematics", "applied mathematics"],
    "engineering": ["engineering", "mechanical engineering", "electrical engineering"],
    "ai": ["artificial intelligence", "machine learning", "deep learning"],
    "agriculture": ["agriculture", "agronomy", "crop science"]
}

# High-impact journal RSS feeds (editors picks, most read, highlights)
JOURNAL_FEEDS = {
    # Nature family
    "nature_highlights": "https://www.nature.com/nature.rss",
    "nature_chem": "https://www.nature.com/nchem.rss",
    "nature_phys": "https://www.nature.com/nphys.rss",
    "nature_bio": "https://www.nature.com/nbt.rss",
    "nature_comm": "https://www.nature.com/ncomms.rss",
    "nat_machine_intel": "https://www.nature.com/natmachintell.rss",
    # Science/AAAS
    "science": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "science_advances": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",
    "science_robotics": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=scirobotics",
    # PNAS
    "pnas": "https://www.pnas.org/rss/current.xml",
    # Cell
    "cell": "https://www.cell.com/cell/inpress.rss",
    "cell_reports": "https://www.cell.com/cell-reports/inpress.rss",
    # Chemistry specific
    "jacs": "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jacsat",
    "angew_chem": "https://onlinelibrary.wiley.com/feed/15213773/most-recent",
    "chem_rev": "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=chreay",
    # Physics
    "phys_rev_lett": "https://feeds.aps.org/rss/recent/prl.xml",
    "phys_rev_x": "https://feeds.aps.org/rss/recent/prx.xml",
    # Engineering
    "ieee_spectrum": "https://spectrum.ieee.org/feeds/feed.rss",
    # Math
    "quanta": "https://api.quantamagazine.org/feed/",
    # Agriculture/Bio
    "plant_cell": "https://academic.oup.com/rss/site_5294/3092.xml",
}

# Map feeds to subjects
FEED_SUBJECT_MAP = {
    "nature_chem": "chemistry", "jacs": "chemistry", "angew_chem": "chemistry", "chem_rev": "chemistry",
    "nature_phys": "physics", "phys_rev_lett": "physics", "phys_rev_x": "physics",
    "nature_bio": "biology", "cell": "biology", "cell_reports": "biology", "plant_cell": "biology",
    "quanta": "mathematics",
    "ieee_spectrum": "engineering", "science_robotics": "engineering",
    "nat_machine_intel": "ai",
    "plant_cell": "agriculture",
    # General feeds map to multiple
    "nature_highlights": "all", "nature_comm": "all", "science": "all",
    "science_advances": "all", "pnas": "all",
}

@dataclass
class Article:
    id: str
    title: str
    abstract: str
    doi: str
    url: str
    pdf_url: Optional[str]
    venue: str
    published: str
    authors: List[str]
    subject: str
    # Scores
    S: int = 0  # Significance
    E: int = 0  # Evidence
    T: int = 0  # Teachability
    M: int = 0  # Media affordance
    H: int = 0  # Hype penalty
    route: str = ""  # indepth/digest/blurb/reject
    course_hooks: List[str] = None
    skill_hooks: List[str] = None

import feedparser
import re
import sys

# Add napkin to path
sys.path.insert(0, "/storage/napkin")
from src.visual_story import generate_story_scenes, generate_visual_story_html

DOI_PATTERN = re.compile(r'\b10\.\d{4,9}/[^\s<>"]+')

def fetch_journal_feeds(target_subject: str = None) -> List[Article]:
    """Fetch articles from high-impact journal RSS feeds"""
    articles = []

    for feed_name, feed_url in JOURNAL_FEEDS.items():
        feed_subject = FEED_SUBJECT_MAP.get(feed_name, "all")

        # Skip if we're targeting a specific subject and this doesn't match
        if target_subject and feed_subject != "all" and feed_subject != target_subject:
            continue

        print(f"   📡 {feed_name}...", end=" ")
        try:
            feed = feedparser.parse(feed_url)
            count = 0

            for entry in feed.entries[:15]:  # Top 15 per feed
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:1000]

                # Extract DOI from link or content
                doi = None
                doi_match = DOI_PATTERN.search(link + " " + summary)
                if doi_match:
                    doi = doi_match.group().rstrip(".,;)")

                if not doi and "doi.org" in link:
                    doi = link.split("doi.org/")[-1]

                if not title:
                    continue

                # Determine subject
                subj = feed_subject if feed_subject != "all" else guess_subject(title + " " + summary)

                articles.append(Article(
                    id=f"rss:{feed_name}:{hash(title) % 100000}",
                    title=title,
                    abstract=summary,
                    doi=doi or "",
                    url=link,
                    pdf_url=None,  # Will lookup via Unpaywall
                    venue=feed_name.replace("_", " ").title(),
                    published=entry.get("published", "")[:10],
                    authors=[],
                    subject=subj
                ))
                count += 1

            print(f"{count} articles")
        except Exception as e:
            print(f"error: {e}")

    return articles


def guess_subject(text: str) -> str:
    """Guess subject from text content"""
    text = text.lower()
    if any(w in text for w in ["chemical", "molecule", "synthesis", "catalyst", "reaction"]):
        return "chemistry"
    if any(w in text for w in ["quantum", "particle", "photon", "laser", "magnetic"]):
        return "physics"
    if any(w in text for w in ["cell", "gene", "protein", "dna", "rna", "genome", "cancer"]):
        return "biology"
    if any(w in text for w in ["neural", "machine learning", "ai ", "deep learning", "llm"]):
        return "ai"
    if any(w in text for w in ["robot", "engineer", "material", "device", "sensor"]):
        return "engineering"
    if any(w in text for w in ["theorem", "proof", "algebra", "topology", "equation"]):
        return "mathematics"
    if any(w in text for w in ["crop", "plant", "soil", "farm", "seed", "yield"]):
        return "agriculture"
    return "biology"  # Default


def lookup_pdf_unpaywall(doi: str) -> Optional[str]:
    """Get PDF URL from Unpaywall"""
    if not doi:
        return None
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email={OPENALEX_EMAIL}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("is_oa"):
                best = data.get("best_oa_location") or {}
                return best.get("url_for_pdf") or best.get("url")
    except:
        pass
    return None


def enrich_with_pdf(articles: List[Article]) -> List[Article]:
    """Add PDF URLs via Unpaywall for articles with DOIs"""
    print(f"   🔍 Looking up PDFs for {len(articles)} articles...")
    found = 0
    for article in articles:
        if article.doi and not article.pdf_url:
            pdf = lookup_pdf_unpaywall(article.doi)
            if pdf:
                article.pdf_url = pdf
                found += 1
    print(f"   ✅ Found {found} PDFs")
    return articles


def ollama_score(article: Article) -> Dict:
    """Score article using rubric via Ollama"""
    prompt = f"""Score this research article for an undergraduate STEM education website.

TITLE: {article.title}

ABSTRACT: {article.abstract[:1500]}

VENUE: {article.venue}

Score each dimension 0-5:

S (Significance): 0=trivial, 3=removes bottleneck, 5=changes what's feasible
E (Evidence): 0=weak/speculative, 3=solid controls, 5=multiple validations
T (Teachability): 0=impossible for undergrads, 3=with scaffolding, 5=ties directly to core concepts
M (Media): 0=no visual angle, 3=one good diagram possible, 5=highly visual
H (Hype Penalty): 0=honest claims, 3=some overselling, 5=breakthrough claims with thin evidence

Also provide:
- 2-3 course_hooks (concepts: kinetics, thermodynamics, eigenvectors, diffusion, Bayes, etc.)
- 1-2 skill_hooks (skills: estimate order-of-magnitude, interpret error bars, etc.)

Respond in JSON only:
{{"S": 4, "E": 4, "T": 5, "M": 3, "H": 1, "course_hooks": ["kinetics", "diffusion"], "skill_hooks": ["interpret rate law"]}}
"""

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }, timeout=120)

        text = resp.json().get("response", "")
        # Extract JSON from response
        import re
        match = re.search(r'\{[^{}]+\}', text)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"  Scoring error: {e}")

    return {"S": 0, "E": 0, "T": 0, "M": 0, "H": 5}

def route_article(a: Article) -> str:
    """Apply routing rules from rubric"""
    # In-Depth: E≥4 AND T≥4 AND (S≥4 OR M≥4) AND H≤2
    if a.E >= 4 and a.T >= 4 and (a.S >= 4 or a.M >= 4) and a.H <= 2:
        return "indepth"
    # Digest: E≥3 AND T≥3 AND (S≥3 OR M≥3) AND H≤3
    if a.E >= 3 and a.T >= 3 and (a.S >= 3 or a.M >= 3) and a.H <= 3:
        return "digest"
    # Blurb: T≥2 AND (S≥3 OR M≥3)
    if a.T >= 2 and (a.S >= 3 or a.M >= 3):
        return "blurb"
    return "reject"

def fetch_openalex(subject: str, concepts: List[str], days: int = 7, limit: int = 50) -> List[Article]:
    """Fetch OA articles from OpenAlex"""
    articles = []
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()

    for concept in concepts[:2]:  # Limit API calls
        params = {
            "filter": f"from_publication_date:{since},is_oa:true",
            "search": concept,
            "per-page": min(limit, 50),
            "mailto": OPENALEX_EMAIL
        }

        try:
            resp = requests.get("https://api.openalex.org/works", params=params, timeout=30)
            data = resp.json()

            for w in data.get("results", []):
                doi = (w.get("doi") or "").replace("https://doi.org/", "")
                if not doi:
                    continue

                # Get PDF URL
                pdf_url = None
                best = w.get("best_oa_location") or {}
                pdf_url = best.get("pdf_url") or best.get("landing_page_url")

                # Reconstruct abstract
                abstract = ""
                inv = w.get("abstract_inverted_index")
                if inv:
                    words = {}
                    for token, positions in inv.items():
                        for p in positions:
                            words[p] = token
                    abstract = " ".join(words[i] for i in sorted(words.keys()))

                authors = []
                for a in (w.get("authorships") or [])[:5]:
                    name = (a.get("author") or {}).get("display_name")
                    if name:
                        authors.append(name)

                venue = (w.get("primary_location") or {}).get("source", {}).get("display_name", "")

                articles.append(Article(
                    id=f"doi:{doi}",
                    title=w.get("title", ""),
                    abstract=abstract[:2000],
                    doi=doi,
                    url=w.get("doi") or "",
                    pdf_url=pdf_url,
                    venue=venue,
                    published=w.get("publication_date", "")[:10],
                    authors=authors,
                    subject=subject
                ))
        except Exception as e:
            print(f"  OpenAlex error for {concept}: {e}")

    return articles

def download_pdf(article: Article) -> Optional[Path]:
    """Download PDF if available"""
    if not article.pdf_url:
        return None

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    filename = hashlib.md5(article.doi.encode()).hexdigest()[:12] + ".pdf"
    path = PDF_DIR / filename

    if path.exists():
        return path

    try:
        resp = requests.get(article.pdf_url, timeout=60, headers={
            "User-Agent": "TheBeakers/1.0 (educational; thebeakerscom@gmail.com)"
        })
        if resp.status_code == 200 and b"%PDF" in resp.content[:10]:
            path.write_bytes(resp.content)
            return path
    except:
        pass

    return None

def generate_indepth(article: Article, pdf_path: Optional[Path]) -> str:
    """Generate In-Depth HTML using napkin visual-story"""
    slug = article.doi.replace("/", "-").replace(".", "-")[:50]
    output_path = DEEPDIVE_DIR / f"{article.subject}-{slug}.html"

    # Build article text for visual story
    article_text = f"""
TITLE: {article.title}

ABSTRACT: {article.abstract}

VENUE: {article.venue}

COURSE HOOKS: {', '.join(article.course_hooks or [])}
SKILL HOOKS: {', '.join(article.skill_hooks or [])}
"""

    try:
        # Use napkin visual story generator
        print(f"         Generating visual story with napkin...")
        scenes = generate_story_scenes(article_text, model=OLLAMA_MODEL)
        html = generate_visual_story_html(scenes, title=article.title)

        # Add The Beakers branding and curriculum connection
        html = add_beakers_branding(html, article)
        output_path.write_text(html)
        return str(output_path)
    except Exception as e:
        print(f"         Napkin error: {e}, using fallback...")

    # Fallback: generate with award-winning template
    prompt = f"""Create an In-Depth educational article for undergraduate students.

TITLE: {article.title}
ABSTRACT: {article.abstract}
VENUE: {article.venue}
COURSE HOOKS: {', '.join(article.course_hooks or [])}

Write in this structure:
1. ONE-SENTENCE CLAIM
2. WHY IT MATTERS (2-3 sentences)
3. THE MECHANISM (3 steps: A → B → C)
4. CURRICULUM BRIDGE (connect to undergrad concepts)
5. WHY TO DOUBT IT (one limitation)
6. TAKEAWAY

Be clear, avoid jargon, write for curious undergrads."""

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=180)
        content = resp.json().get("response", "")
    except:
        content = article.abstract

    # Generate HTML
    html = generate_award_html(article, content, "indepth")
    output_path.write_text(html)
    return str(output_path)


def add_beakers_branding(html: str, article: Article) -> str:
    """Add The Beakers header, footer, and curriculum connection to napkin HTML"""
    # Insert header after <body>
    header = '''
    <header style="position:fixed;top:0;left:0;right:0;z-index:100;padding:1rem 2rem;backdrop-filter:blur(20px);background:rgba(15,23,42,0.9);border-bottom:1px solid #334155;display:flex;justify-content:space-between;align-items:center;">
        <a href="/" style="font-family:'Instrument Serif',serif;font-size:1.5rem;color:#e2e8f0;text-decoration:none;">The <span style="color:#10b981;">Beakers</span></a>
        <nav>
            <a href="/chemistry.html" style="color:#94a3b8;text-decoration:none;margin-left:2rem;font-size:0.9rem;">Chemistry</a>
            <a href="/deepdive/" style="color:#94a3b8;text-decoration:none;margin-left:2rem;font-size:0.9rem;">Deep Dives</a>
        </nav>
    </header>
    <div style="height:70px;"></div>
    '''

    # Curriculum connection section
    course_tags = "".join(f'<span style="display:inline-block;padding:0.3rem 0.8rem;background:#1e293b;border:1px solid #334155;border-radius:100px;font-size:0.8rem;color:#94a3b8;margin:0.25rem;">{h}</span>' for h in (article.course_hooks or []))
    skill_tags = "".join(f'<span style="display:inline-block;padding:0.3rem 0.8rem;background:#1e293b;border:1px solid #10b981;border-radius:100px;font-size:0.8rem;color:#10b981;margin:0.25rem;">{h}</span>' for h in (article.skill_hooks or []))

    curriculum = f'''
    <div style="max-width:1100px;margin:0 auto;padding:2rem;">
        <div style="background:#1e293b;border:1px solid #334155;border-radius:16px;padding:2rem;margin-bottom:2rem;">
            <h2 style="font-size:1.5rem;color:#10b981;margin-bottom:1rem;display:flex;align-items:center;gap:0.75rem;">
                <span>🎓</span> Curriculum Connection
            </h2>
            <p style="color:#94a3b8;margin-bottom:1rem;">Connect this research to your coursework:</p>
            <div style="display:flex;flex-wrap:wrap;gap:0.5rem;">
                {course_tags}{skill_tags}
            </div>
        </div>
        <div style="text-align:center;">
            <a href="{article.url}" target="_blank" style="display:inline-flex;align-items:center;gap:0.5rem;padding:1rem 2rem;background:#10b981;color:#0f172a;text-decoration:none;font-weight:600;border-radius:100px;">
                Read Original Paper →
            </a>
        </div>
    </div>
    '''

    # Replace footer
    new_footer = f'''
    <footer style="text-align:center;padding:3rem 2rem;color:#94a3b8;font-size:0.85rem;border-top:1px solid #334155;">
        <p>The Beakers — Research, Rewritten for Students</p>
        <p style="margin-top:0.5rem;">© {datetime.now().year} The Beakers</p>
    </footer>
    '''

    # Insert header after <body>
    html = html.replace('<body>', '<body>' + header)

    # Add curriculum before footer
    html = html.replace('<footer>', curriculum + '<footer>')

    # Replace footer content
    import re
    html = re.sub(r'<footer>.*?</footer>', new_footer, html, flags=re.DOTALL)

    return html

def generate_digest(article: Article) -> str:
    """Generate Digest visual summary using napkin style"""
    slug = article.doi.replace("/", "-").replace(".", "-")[:50]
    output_path = DEEPDIVE_DIR / f"{article.subject}-{slug}-visual.html"

    # Generate visual summary content
    prompt = f"""Create a visual summary for undergrads.

TITLE: {article.title}
ABSTRACT: {article.abstract}

Provide:
1. TL;DR (2 sentences max)
2. KEY FINDING (1 sentence)
3. WHY IT MATTERS (1 sentence)
4. COURSE CONNECTION (which undergrad course concepts apply)
5. ONE CAUTION (limitation)

Be extremely concise."""

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=120)
        content = resp.json().get("response", "")
    except:
        content = article.abstract[:500]

    html = generate_award_html(article, content, "digest")
    output_path.write_text(html)
    return str(output_path)

def generate_blurb(article: Article) -> Dict:
    """Generate blurb data (for index page)"""
    return {
        "id": article.id,
        "title": article.title,
        "tldr": article.abstract[:200] + "..." if len(article.abstract) > 200 else article.abstract,
        "course_hooks": article.course_hooks or [],
        "url": article.url,
        "venue": article.venue,
        "subject": article.subject
    }

def generate_award_html(article: Article, content: str, style: str) -> str:
    """Generate award-winning HTML with animations"""

    accent = {
        "chemistry": "#10b981",
        "physics": "#3b82f6",
        "biology": "#22c55e",
        "mathematics": "#8b5cf6",
        "engineering": "#f59e0b",
        "ai": "#06b6d4",
        "agriculture": "#84cc16"
    }.get(article.subject, "#10b981")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article.title} | The Beakers</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0a0a0f;
            --bg-card: #12121a;
            --bg-elevated: #1a1a24;
            --text: #f0f0f5;
            --text-muted: #8888a0;
            --accent: {accent};
            --accent-glow: {accent}40;
            --border: #2a2a3a;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        html {{ scroll-behavior: smooth; }}

        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* Animated gradient background */
        .bg-gradient {{
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse 80% 50% at 20% 40%, var(--accent-glow), transparent),
                radial-gradient(ellipse 60% 40% at 80% 60%, #3b82f620, transparent);
            pointer-events: none;
            z-index: -1;
            animation: pulse 8s ease-in-out infinite alternate;
        }}

        @keyframes pulse {{
            0% {{ opacity: 0.5; transform: scale(1); }}
            100% {{ opacity: 0.8; transform: scale(1.1); }}
        }}

        /* Grain texture */
        .grain {{
            position: fixed;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            opacity: 0.03;
            pointer-events: none;
            z-index: -1;
        }}

        /* Header */
        header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(20px);
            background: rgba(10,10,15,0.8);
            border-bottom: 1px solid var(--border);
            z-index: 100;
        }}

        .logo {{
            font-family: 'Instrument Serif', serif;
            font-size: 1.5rem;
            font-weight: 400;
            color: var(--text);
            text-decoration: none;
            letter-spacing: -0.02em;
        }}

        .logo span {{ color: var(--accent); }}

        nav a {{
            color: var(--text-muted);
            text-decoration: none;
            margin-left: 2rem;
            font-size: 0.9rem;
            transition: color 0.2s;
        }}

        nav a:hover {{ color: var(--accent); }}

        /* Hero */
        .hero {{
            padding: 8rem 2rem 4rem;
            max-width: 900px;
            margin: 0 auto;
            text-align: center;
        }}

        .badge {{
            display: inline-block;
            padding: 0.4rem 1rem;
            background: var(--accent-glow);
            border: 1px solid var(--accent);
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--accent);
            margin-bottom: 1.5rem;
            animation: fadeInUp 0.6s ease-out;
        }}

        h1 {{
            font-family: 'Instrument Serif', serif;
            font-size: clamp(2rem, 5vw, 3.5rem);
            font-weight: 400;
            line-height: 1.2;
            letter-spacing: -0.02em;
            margin-bottom: 1.5rem;
            animation: fadeInUp 0.6s ease-out 0.1s both;
        }}

        .meta {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            color: var(--text-muted);
            font-size: 0.9rem;
            animation: fadeInUp 0.6s ease-out 0.2s both;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* Content */
        .content {{
            max-width: 720px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 1.5rem;
            padding: 2.5rem;
            margin-bottom: 2rem;
            animation: fadeInUp 0.6s ease-out 0.3s both;
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3), 0 0 0 1px var(--accent);
        }}

        .card h2 {{
            font-family: 'Instrument Serif', serif;
            font-size: 1.5rem;
            font-weight: 400;
            margin-bottom: 1rem;
            color: var(--accent);
        }}

        .card p {{
            color: var(--text-muted);
            margin-bottom: 1rem;
        }}

        .card p:last-child {{ margin-bottom: 0; }}

        /* Tags */
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1.5rem;
        }}

        .tag {{
            padding: 0.3rem 0.8rem;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 100px;
            font-size: 0.8rem;
            color: var(--text-muted);
            transition: all 0.2s;
        }}

        .tag:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}

        /* CTA Button */
        .cta {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            background: var(--accent);
            color: var(--bg);
            text-decoration: none;
            font-weight: 600;
            border-radius: 100px;
            transition: all 0.3s;
            margin-top: 1rem;
        }}

        .cta:hover {{
            transform: scale(1.05);
            box-shadow: 0 0 30px var(--accent-glow);
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 4rem;
        }}

        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            header {{ padding: 1rem; }}
            nav a {{ margin-left: 1rem; font-size: 0.8rem; }}
            .hero {{ padding: 6rem 1rem 2rem; }}
            .content {{ padding: 1rem; }}
            .card {{ padding: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="bg-gradient"></div>
    <div class="grain"></div>

    <header>
        <a href="/" class="logo">The <span>Beakers</span></a>
        <nav>
            <a href="/{article.subject}.html">{article.subject.title()}</a>
            <a href="/deepdive/">Deep Dives</a>
        </nav>
    </header>

    <main>
        <section class="hero">
            <span class="badge">{style.upper()} · {article.subject.upper()}</span>
            <h1>{article.title}</h1>
            <div class="meta">
                <span class="meta-item">📅 {article.published}</span>
                <span class="meta-item">📰 {article.venue}</span>
            </div>
        </section>

        <section class="content">
            <article class="card">
                <h2>Summary</h2>
                {"".join(f"<p>{p}</p>" for p in content.split(chr(10)+chr(10)) if p.strip())}
            </article>

            <article class="card">
                <h2>Curriculum Connection</h2>
                <p>Connect this research to your coursework:</p>
                <div class="tags">
                    {"".join(f'<span class="tag">{h}</span>' for h in (article.course_hooks or []))}
                    {"".join(f'<span class="tag">{h}</span>' for h in (article.skill_hooks or []))}
                </div>
            </article>

            <div style="text-align: center;">
                <a href="{article.url}" class="cta" target="_blank">
                    Read Original Paper →
                </a>
            </div>
        </section>
    </main>

    <footer>
        <p>The Beakers — Research, Rewritten for Students</p>
        <p style="margin-top: 0.5rem;">© {datetime.now().year} The Beakers</p>
    </footer>
</body>
</html>'''


def run_weekly(subjects: List[str] = None, days: int = 7):
    """
    Run the full weekly pipeline

    Per subject:
    - 1 Deep candidate (for NotebookLM - manual)
    - 5 Explain (automated detailed articles)
    - 10 Digest (automated TL;DRs)

    Plus 1 Education highlight per week
    """
    subjects = subjects or list(SUBJECTS.keys())

    print(f"🧪 The Beakers Weekly Pipeline")
    print(f"   Subjects: {', '.join(subjects)}")
    print(f"   Lookback: {days} days")
    print(f"\n   Output per subject: 1 Deep (manual) | 5 Explain | 10 Digest")
    print()

    # Ensure directories exist
    for d in [DATA_DIR, CONTENT_DIR, ISSUES_DIR, NOTES_DIR, DEEPDIVE_DIR, PDF_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    week_of = datetime.now().strftime("%Y-%m-%d")
    weekly_report = {"week": week_of, "subjects": {}}
    all_digests = []

    for subject in subjects:
        print(f"\n{'='*60}")
        print(f"📚 {subject.upper()}")
        print(f"{'='*60}")
        concepts = SUBJECTS.get(subject, [subject])

        # Fetch from multiple sources - cast a wide net!
        print(f"\n   📥 COLLECTING ARTICLES")

        # 1. High-impact journal RSS feeds (Nature, Science, Cell, etc.)
        print(f"   From journal RSS feeds:")
        rss_articles = fetch_journal_feeds(subject)
        rss_articles = [a for a in rss_articles if a.subject == subject]

        # 2. OpenAlex OA articles
        print(f"   From OpenAlex OA...")
        oa_articles = fetch_openalex(subject, concepts, days, limit=50)

        # Combine and dedupe by title
        seen_titles = set()
        articles = []
        for a in rss_articles + oa_articles:
            title_key = a.title.lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                articles.append(a)

        print(f"   📊 Total unique: {len(articles)} articles")

        # Enrich with PDF URLs via Unpaywall
        articles = enrich_with_pdf([a for a in articles if a.doi])

        if not articles:
            continue

        # Score all articles
        scored = []
        for i, article in enumerate(articles[:40]):  # Score top 40
            print(f"   Scoring {i+1}/40: {article.title[:45]}...", end=" ")

            scores = ollama_score(article)
            article.S = scores.get("S", 0)
            article.E = scores.get("E", 0)
            article.T = scores.get("T", 0)
            article.M = scores.get("M", 0)
            article.H = scores.get("H", 5)
            article.course_hooks = scores.get("course_hooks", [])
            article.skill_hooks = scores.get("skill_hooks", [])

            # Calculate composite score
            composite = (article.S + article.E + article.T + article.M) - article.H
            print(f"[{composite}]")
            scored.append((composite, article))

        # Sort by composite score
        scored.sort(key=lambda x: x[0], reverse=True)

        # Route: Top 1 = Deep candidate, Next 5 = Explain, Next 10 = Digest
        deep_candidate = scored[0][1] if len(scored) > 0 else None
        explain_articles = [a for _, a in scored[1:6]]  # 5 explain
        digest_articles = [a for _, a in scored[6:16]]  # 10 digest

        subject_report = {
            "deep_candidate": None,
            "explain": [],
            "digest": []
        }

        # === DEEP CANDIDATE (for NotebookLM - manual) ===
        if deep_candidate:
            print(f"\n   🎯 DEEP CANDIDATE (for NotebookLM):")
            print(f"      Title: {deep_candidate.title}")
            print(f"      DOI: {deep_candidate.doi}")

            # Create subject folder for Deep
            deep_folder = DEEP_DIR / subject
            deep_folder.mkdir(parents=True, exist_ok=True)

            # Download PDF
            pdf_path = None
            if deep_candidate.pdf_url:
                pdf_path = deep_folder / "article.pdf"
                try:
                    resp = requests.get(deep_candidate.pdf_url, timeout=60, headers={
                        "User-Agent": "TheBeakers/1.0 (educational)"
                    })
                    if resp.status_code == 200 and b"%PDF" in resp.content[:10]:
                        pdf_path.write_bytes(resp.content)
                        print(f"      📥 PDF: {pdf_path}")
                except Exception as e:
                    print(f"      ⚠️  PDF download failed: {e}")
                    pdf_path = None

            # Create manifest.json for user to fill in
            manifest = {
                "title": deep_candidate.title,
                "doi": deep_candidate.doi,
                "url": deep_candidate.url,
                "venue": deep_candidate.venue,
                "published": deep_candidate.published,
                "authors": deep_candidate.authors,
                "subject": subject,
                "scores": {
                    "S": deep_candidate.S,
                    "E": deep_candidate.E,
                    "T": deep_candidate.T,
                    "M": deep_candidate.M,
                    "H": deep_candidate.H
                },
                "course_hooks": deep_candidate.course_hooks,
                "skill_hooks": deep_candidate.skill_hooks,
                # === USER FILLS THESE IN ===
                "youtube_url": "",      # Paste YouTube URL here
                "soundcloud_url": "",   # Paste SoundCloud URL here
                "status": "pending"     # Change to "ready" when done
            }

            manifest_path = deep_folder / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            print(f"      📋 Manifest: {manifest_path}")

            # Create README for user
            readme = f"""# Deep Dive: {subject.title()}

## Article
**{deep_candidate.title}**

DOI: {deep_candidate.doi}
Venue: {deep_candidate.venue}

## Your Workflow

1. ✅ PDF downloaded (article.pdf)
2. ⬜ Upload to NotebookLM
3. ⬜ Generate podcast → Upload to SoundCloud → Paste URL in manifest.json
4. ⬜ Generate video → Upload to YouTube → Paste URL in manifest.json
5. ⬜ Download study guide → Save as study_guide.pdf
6. ⬜ Set "status": "ready" in manifest.json

## Files to Add
- study_guide.pdf (from NotebookLM)
- Any extra images/figures

## Generate Final HTML
```bash
python3 scripts/weekly_pipeline.py --build-deep {subject}
```
"""
            (deep_folder / "README.md").write_text(readme)
            print(f"      📖 README: {deep_folder}/README.md")

            subject_report["deep_candidate"] = {
                "title": deep_candidate.title,
                "doi": deep_candidate.doi,
                "folder": str(deep_folder),
                "manifest": str(manifest_path),
                "pdf": str(pdf_path) if pdf_path else None
            }

        # === EXPLAIN (5 automated detailed articles) ===
        print(f"\n   📝 EXPLAIN (5 detailed articles):")
        for i, article in enumerate(explain_articles, 1):
            print(f"      {i}. {article.title[:50]}...")
            output = generate_indepth(article, None)
            print(f"         → {output}")
            subject_report["explain"].append({
                "title": article.title,
                "doi": article.doi,
                "file": output,
                "course_hooks": article.course_hooks
            })

        # === DIGEST (10 TL;DRs) ===
        print(f"\n   📋 DIGEST (10 TL;DRs):")
        for i, article in enumerate(digest_articles, 1):
            print(f"      {i}. {article.title[:50]}...")
            digest_data = generate_blurb(article)
            digest_data["subject"] = subject
            all_digests.append(digest_data)
            subject_report["digest"].append({
                "title": article.title,
                "doi": article.doi,
                "tldr": digest_data["tldr"],
                "course_hooks": article.course_hooks
            })

        weekly_report["subjects"][subject] = subject_report
        print(f"\n   ✅ {subject}: 1 deep candidate, {len(explain_articles)} explain, {len(digest_articles)} digest")

    # === EDUCATION HIGHLIGHT (1 per week) ===
    print(f"\n{'='*60}")
    print(f"🎓 EDUCATION HIGHLIGHT")
    print(f"{'='*60}")
    edu_article = generate_education_highlight()
    weekly_report["education"] = edu_article

    # Save weekly report
    report_path = DATA_DIR / f"weekly_report_{week_of}.json"
    with open(report_path, "w") as f:
        json.dump(weekly_report, f, indent=2)
    print(f"\n📊 Weekly report → {report_path}")

    # Save all digests
    digests_path = DATA_DIR / f"digests_{week_of}.json"
    with open(digests_path, "w") as f:
        json.dump(all_digests, f, indent=2)
    print(f"📋 All digests ({len(all_digests)}) → {digests_path}")

    # Print summary for NotebookLM work
    print(f"\n{'='*60}")
    print(f"📌 DEEP CANDIDATES FOR NOTEBOOKLM:")
    print(f"{'='*60}")
    for subj, data in weekly_report["subjects"].items():
        if data.get("deep_candidate"):
            dc = data["deep_candidate"]
            print(f"\n   [{subj.upper()}]")
            print(f"   Title: {dc['title']}")
            print(f"   PDF: {dc.get('pdf_local') or dc.get('pdf_url') or 'Find manually'}")

    print(f"\n🎉 Pipeline complete!")
    return weekly_report


def generate_education_highlight() -> Dict:
    """Generate weekly education highlight - a teaching move or misconception killer"""
    prompt = """Generate an education highlight for STEM undergrads.

Pick ONE of these formats:
1. MISCONCEPTION KILLER: A common wrong belief and how to fix it
2. TEACHING MOVE: A technique that makes a hard concept click
3. SKILL BUILDER: A practice that improves scientific thinking

Respond in JSON:
{
    "type": "misconception|teaching_move|skill",
    "title": "Short catchy title",
    "misconception": "What students wrongly believe (if applicable)",
    "why_wrong": "Why it's wrong",
    "correct_model": "The right way to think about it",
    "classroom_move": "What to do in 10 minutes",
    "exit_questions": ["Question 1?", "Question 2?"]
}
"""

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=120)

        text = resp.json().get("response", "")
        import re
        match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"   Education highlight error: {e}")

    return {
        "type": "teaching_move",
        "title": "Order of Magnitude Estimation",
        "classroom_move": "Have students estimate before calculating",
        "exit_questions": ["Is 10^6 closer to a million or billion?", "Estimate the number of cells in your body"]
    }


def build_deep(subject: str):
    """
    Build Deep Dive HTML from completed folder.
    Reads manifest.json and generates final HTML with all embeds.
    """
    deep_folder = DEEP_DIR / subject
    manifest_path = deep_folder / "manifest.json"

    if not manifest_path.exists():
        print(f"❌ No manifest found at {manifest_path}")
        print(f"   Run the weekly pipeline first to create Deep candidates.")
        return False

    with open(manifest_path) as f:
        manifest = json.load(f)

    if manifest.get("status") != "ready":
        print(f"⚠️  Status is '{manifest.get('status')}', not 'ready'")
        print(f"   Fill in youtube_url and soundcloud_url in manifest.json")
        print(f"   Then set status to 'ready'")
        return False

    youtube_url = manifest.get("youtube_url", "")
    soundcloud_url = manifest.get("soundcloud_url", "")

    if not youtube_url:
        print("❌ Missing youtube_url in manifest.json")
        return False

    # Extract YouTube video ID
    import re
    yt_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', youtube_url)
    yt_id = yt_match.group(1) if yt_match else ""

    # Extract SoundCloud embed (or use URL directly)
    sc_embed = soundcloud_url

    print(f"🔨 Building Deep Dive: {subject}")
    print(f"   Title: {manifest['title']}")
    print(f"   YouTube: {yt_id}")
    print(f"   SoundCloud: {'✓' if soundcloud_url else '✗'}")

    # Generate the Deep Dive HTML
    slug = manifest['doi'].replace("/", "-").replace(".", "-")[:50]
    output_path = DEEPDIVE_DIR / f"{subject}-{slug}-deep.html"

    accent = {
        "chemistry": "#10b981", "physics": "#3b82f6", "biology": "#22c55e",
        "mathematics": "#8b5cf6", "engineering": "#f59e0b", "ai": "#06b6d4",
        "agriculture": "#84cc16"
    }.get(subject, "#10b981")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{manifest["title"]} | Deep Dive | The Beakers</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0a0a0f;
            --bg-card: #12121a;
            --text: #f0f0f5;
            --text-muted: #8888a0;
            --accent: {accent};
            --accent-glow: {accent}40;
            --border: #2a2a3a;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
        }}
        .bg-gradient {{
            position: fixed; inset: 0; z-index: -1;
            background: radial-gradient(ellipse 80% 50% at 20% 40%, var(--accent-glow), transparent);
            animation: pulse 8s ease-in-out infinite alternate;
        }}
        @keyframes pulse {{ 0% {{ opacity: 0.5; }} 100% {{ opacity: 0.8; }} }}

        header {{
            position: fixed; top: 0; left: 0; right: 0; z-index: 100;
            padding: 1rem 2rem;
            backdrop-filter: blur(20px);
            background: rgba(10,10,15,0.8);
            border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
        }}
        .logo {{ font-family: 'Instrument Serif', serif; font-size: 1.5rem; color: var(--text); text-decoration: none; }}
        .logo span {{ color: var(--accent); }}

        .hero {{
            padding: 8rem 2rem 3rem;
            max-width: 900px; margin: 0 auto; text-align: center;
        }}
        .badge {{
            display: inline-block; padding: 0.4rem 1rem;
            background: var(--accent-glow); border: 1px solid var(--accent);
            border-radius: 100px; font-size: 0.75rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.1em; color: var(--accent);
            margin-bottom: 1.5rem;
        }}
        h1 {{
            font-family: 'Instrument Serif', serif;
            font-size: clamp(2rem, 5vw, 3rem);
            font-weight: 400; line-height: 1.2; margin-bottom: 1rem;
        }}
        .meta {{ color: var(--text-muted); font-size: 0.9rem; }}

        .content {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}

        .section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 1.5rem;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        .section h2 {{
            font-family: 'Instrument Serif', serif;
            font-size: 1.5rem; color: var(--accent);
            margin-bottom: 1.5rem;
            display: flex; align-items: center; gap: 0.75rem;
        }}
        .section h2::before {{
            content: attr(data-icon);
            font-size: 1.2rem;
        }}

        .video-container {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            border-radius: 1rem;
            overflow: hidden;
        }}
        .video-container iframe {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            border: none;
        }}

        .audio-container {{
            border-radius: 1rem;
            overflow: hidden;
        }}
        .audio-container iframe {{
            width: 100%;
            border: none;
        }}

        .tags {{
            display: flex; flex-wrap: wrap; gap: 0.5rem;
            margin-top: 1rem;
        }}
        .tag {{
            padding: 0.3rem 0.8rem;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 100px;
            font-size: 0.8rem;
            color: var(--text-muted);
        }}

        footer {{
            text-align: center;
            padding: 3rem 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
        }}

        @media (max-width: 768px) {{
            header {{ padding: 1rem; }}
            .hero {{ padding: 6rem 1rem 2rem; }}
            .content {{ padding: 1rem; }}
            .section {{ padding: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="bg-gradient"></div>

    <header>
        <a href="/" class="logo">The <span>Beakers</span></a>
    </header>

    <main>
        <section class="hero">
            <span class="badge">DEEP DIVE · {subject.upper()}</span>
            <h1>{manifest["title"]}</h1>
            <p class="meta">{manifest["venue"]} · {manifest["published"]}</p>
        </section>

        <section class="content">
            <!-- VIDEO -->
            <div class="section">
                <h2 data-icon="🎬">Video Explainer</h2>
                <div class="video-container">
                    <iframe src="https://www.youtube.com/embed/{yt_id}" allowfullscreen></iframe>
                </div>
            </div>

            <!-- PODCAST -->
            {"" if not soundcloud_url else f'''
            <div class="section">
                <h2 data-icon="🎧">Podcast</h2>
                <div class="audio-container">
                    <iframe width="100%" height="166" scrolling="no" frameborder="no"
                        src="https://w.soundcloud.com/player/?url={soundcloud_url}&color=%23{accent[1:]}&auto_play=false&hide_related=true&show_comments=false&show_user=true&show_reposts=false&show_teaser=false"></iframe>
                </div>
            </div>
            '''}

            <!-- CURRICULUM CONNECTION -->
            <div class="section">
                <h2 data-icon="🎓">Curriculum Connection</h2>
                <p style="color: var(--text-muted); margin-bottom: 1rem;">
                    Connect this research to your coursework:
                </p>
                <div class="tags">
                    {"".join(f'<span class="tag">{h}</span>' for h in (manifest.get("course_hooks") or []))}
                    {"".join(f'<span class="tag">{h}</span>' for h in (manifest.get("skill_hooks") or []))}
                </div>
            </div>

            <!-- SOURCE -->
            <div class="section">
                <h2 data-icon="📄">Source</h2>
                <p style="color: var(--text-muted);">
                    <strong>{manifest["title"]}</strong><br>
                    {", ".join(manifest.get("authors", [])[:3])}{"..." if len(manifest.get("authors", [])) > 3 else ""}<br>
                    <em>{manifest["venue"]}</em>, {manifest["published"]}<br>
                    <a href="{manifest["url"]}" style="color: var(--accent);">DOI: {manifest["doi"]}</a>
                </p>
            </div>
        </section>
    </main>

    <footer>
        <p>The Beakers — Research, Rewritten for Students</p>
    </footer>
</body>
</html>'''

    output_path.write_text(html)
    print(f"\n✅ Deep Dive generated: {output_path}")
    print(f"   View: https://thebeakers.com/deepdive/{output_path.name}")

    return True


def list_deep_status():
    """Show status of all Deep folders"""
    print("\n📋 DEEP DIVE STATUS")
    print("=" * 60)

    if not DEEP_DIR.exists():
        print("   No Deep folders yet. Run weekly pipeline first.")
        return

    for subject_dir in sorted(DEEP_DIR.iterdir()):
        if not subject_dir.is_dir():
            continue

        manifest_path = subject_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                m = json.load(f)
            status = m.get("status", "unknown")
            title = m.get("title", "")[:40]
            yt = "✓" if m.get("youtube_url") else "✗"
            sc = "✓" if m.get("soundcloud_url") else "✗"
            print(f"\n   [{subject_dir.name.upper()}] {status.upper()}")
            print(f"   {title}...")
            print(f"   YouTube: {yt}  SoundCloud: {sc}")
        else:
            print(f"\n   [{subject_dir.name.upper()}] NO MANIFEST")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="The Beakers Weekly Pipeline")
    parser.add_argument("--subjects", nargs="+", help="Subjects to process (default: all)")
    parser.add_argument("--days", type=int, default=7, help="Lookback days (default: 7)")
    parser.add_argument("--build-deep", metavar="SUBJECT", help="Build Deep Dive HTML from completed folder")
    parser.add_argument("--status", action="store_true", help="Show status of Deep folders")
    args = parser.parse_args()

    if args.status:
        list_deep_status()
    elif args.build_deep:
        build_deep(args.build_deep)
    else:
        print("""
╔══════════════════════════════════════════════════════════════╗
║           THE BEAKERS - WEEKLY CONTENT PIPELINE              ║
╠══════════════════════════════════════════════════════════════╣
║  Per Subject:                                                ║
║    • 1 Deep candidate → data/deep/{subject}/                 ║
║      (YOU process with NotebookLM)                           ║
║    • 5 Explain articles (automated)                          ║
║    • 10 Digest TL;DRs (automated)                            ║
║                                                              ║
║  Plus: 1 Education highlight per week                        ║
║                                                              ║
║  After NotebookLM:                                           ║
║    python3 weekly_pipeline.py --build-deep chemistry         ║
╚══════════════════════════════════════════════════════════════╝
        """)
        run_weekly(args.subjects, args.days)
