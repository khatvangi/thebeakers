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

    # Use napkin visual-story if PDF available
    if pdf_path and pdf_path.exists():
        cmd = f'cd /storage/napkin && python cli.py visual-story --pdf "{pdf_path}" --title "{article.title}" -o "{output_path}"'
        os.system(cmd)
        if output_path.exists():
            return str(output_path)

    # Fallback: generate with Ollama
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


def run_weekly(subjects: List[str] = None, days: int = 7, limit_per_subject: int = 30):
    """Run the full weekly pipeline"""
    subjects = subjects or list(SUBJECTS.keys())

    print(f"🧪 The Beakers Weekly Pipeline")
    print(f"   Subjects: {', '.join(subjects)}")
    print(f"   Lookback: {days} days")
    print()

    # Ensure directories exist
    for d in [DATA_DIR, CONTENT_DIR, ISSUES_DIR, NOTES_DIR, DEEPDIVE_DIR, PDF_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    week_of = datetime.now().strftime("%Y-%m-%d")
    all_blurbs = []

    for subject in subjects:
        print(f"\n📚 {subject.upper()}")
        concepts = SUBJECTS.get(subject, [subject])

        # Fetch articles
        print(f"   Fetching from OpenAlex...")
        articles = fetch_openalex(subject, concepts, days, limit_per_subject)
        print(f"   Found {len(articles)} OA articles")

        if not articles:
            continue

        # Score and route
        indepth_candidates = []
        digest_candidates = []
        blurb_candidates = []

        for i, article in enumerate(articles[:20]):  # Limit scoring
            print(f"   Scoring {i+1}/{min(len(articles), 20)}: {article.title[:50]}...")

            scores = ollama_score(article)
            article.S = scores.get("S", 0)
            article.E = scores.get("E", 0)
            article.T = scores.get("T", 0)
            article.M = scores.get("M", 0)
            article.H = scores.get("H", 5)
            article.course_hooks = scores.get("course_hooks", [])
            article.skill_hooks = scores.get("skill_hooks", [])
            article.route = route_article(article)

            if article.route == "indepth":
                indepth_candidates.append(article)
            elif article.route == "digest":
                digest_candidates.append(article)
            elif article.route == "blurb":
                blurb_candidates.append(article)

            print(f"      → {article.route} (S={article.S} E={article.E} T={article.T} M={article.M} H={article.H})")

        # Generate content
        print(f"\n   Generating content...")

        # 1 In-Depth (best candidate)
        if indepth_candidates:
            best = max(indepth_candidates, key=lambda a: a.S + a.E + a.T + a.M - a.H)
            print(f"   📝 In-Depth: {best.title[:50]}...")
            pdf_path = download_pdf(best)
            output = generate_indepth(best, pdf_path)
            print(f"      → {output}")

        # 3-5 Digest
        for article in digest_candidates[:5]:
            print(f"   📊 Digest: {article.title[:50]}...")
            output = generate_digest(article)
            print(f"      → {output}")

        # Blurbs (collect for index)
        for article in blurb_candidates[:15]:
            all_blurbs.append(generate_blurb(article))

        print(f"\n   ✅ {subject}: {len(indepth_candidates)} in-depth, {len(digest_candidates)} digest, {len(blurb_candidates)} blurbs")

    # Save blurbs index
    blurbs_path = DATA_DIR / f"blurbs_{week_of}.json"
    with open(blurbs_path, "w") as f:
        json.dump(all_blurbs, f, indent=2)
    print(f"\n📋 Saved {len(all_blurbs)} blurbs → {blurbs_path}")

    print("\n🎉 Pipeline complete!")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="The Beakers Weekly Pipeline")
    parser.add_argument("--subjects", nargs="+", help="Subjects to process")
    parser.add_argument("--days", type=int, default=7, help="Lookback days")
    parser.add_argument("--limit", type=int, default=30, help="Articles per subject")
    args = parser.parse_args()

    run_weekly(args.subjects, args.days, args.limit)
