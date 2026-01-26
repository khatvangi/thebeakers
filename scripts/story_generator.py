#!/usr/bin/env python3
"""
story_generator.py - generate visual stories from collected papers

takes papers from society_papers database and generates visual story HTML files.
downloads PDFs and extracts full text for better story generation.

usage:
    python story_generator.py                    # generate for all disciplines
    python story_generator.py chemistry          # generate for one discipline
    python story_generator.py --list             # list papers ready to process
    python story_generator.py --count 3          # generate 3 per discipline
    python story_generator.py --download-only    # just download PDFs, don't generate
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import requests

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("[!] PyMuPDF not available - will use abstracts only")

# paths
SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
DB_PATH = PROJECT_DIR / "data" / "articles.db"
OUTPUT_DIR = PROJECT_DIR / "deepdive"
PDF_DIR = PROJECT_DIR / "data" / "pdfs"
CURRICULUM_PATH = PROJECT_DIR / "data" / "curriculum.json"

# ollama config
OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.2:3b"

# http headers
HEADERS = {
    "User-Agent": "TheBeakers/1.0 (Educational; mailto:thebeakerscom@gmail.com)"
}

# discipline colors
COLORS = {
    "chemistry": "#10b981",
    "physics": "#3b82f6",
    "biology": "#22c55e",
    "mathematics": "#8b5cf6",
    "engineering": "#f59e0b",
    "ai": "#06b6d4",
    "agriculture": "#84cc16"
}


@dataclass
class Paper:
    doi: str
    title: str
    abstract: str
    discipline: str
    journal: str
    url: str
    pdf_url: Optional[str] = None
    full_text: Optional[str] = None  # extracted from PDF


def get_unpaywall_pdf(doi: str) -> Optional[str]:
    """get OA PDF url from Unpaywall"""
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email=thebeakerscom@gmail.com"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # find best OA location
            locations = data.get("oa_locations", [])
            for loc in locations:
                if loc.get("url_for_pdf"):
                    return loc["url_for_pdf"]
            # fallback to landing page
            if locations:
                return locations[0].get("url")
    except Exception as e:
        print(f"  [!] unpaywall error: {e}")
    return None


def download_pdf(paper: Paper) -> Optional[Path]:
    """download PDF for a paper, return path if successful"""
    pdf_dir = PDF_DIR / paper.discipline
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # clean doi for filename
    safe_doi = paper.doi.replace("/", "_").replace(":", "_")
    pdf_path = pdf_dir / f"{safe_doi}.pdf"

    if pdf_path.exists():
        return pdf_path

    # try to get PDF URL
    pdf_url = paper.pdf_url
    if not pdf_url:
        pdf_url = get_unpaywall_pdf(paper.doi)

    if not pdf_url:
        return None

    try:
        print(f"  downloading PDF...", end=" ", flush=True)
        resp = requests.get(pdf_url, headers=HEADERS, timeout=60, allow_redirects=True)
        resp.raise_for_status()

        # verify it's actually a PDF
        if resp.content[:4] != b'%PDF':
            print("not a valid PDF")
            return None

        pdf_path.write_bytes(resp.content)
        print(f"OK ({len(resp.content) // 1024}KB)")
        return pdf_path
    except Exception as e:
        print(f"failed: {e}")
        return None


def extract_pdf_text(pdf_path: Path, max_chars: int = 15000) -> Optional[str]:
    """extract text from PDF using PyMuPDF"""
    if not HAS_PYMUPDF:
        return None

    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        total_chars = 0

        for page in doc:
            page_text = page.get_text()
            text_parts.append(page_text)
            total_chars += len(page_text)
            if total_chars > max_chars:
                break

        doc.close()

        full_text = "\n".join(text_parts)
        # clean up common PDF artifacts
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        full_text = re.sub(r' {2,}', ' ', full_text)

        return full_text[:max_chars]
    except Exception as e:
        print(f"  [!] PDF extraction error: {e}")
        return None


def get_papers(discipline: Optional[str] = None, limit: int = 5, require_abstract: bool = False) -> List[Paper]:
    """get unprocessed papers from database"""
    if not DB_PATH.exists():
        print("[!] database not found")
        return []

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # get papers - if not requiring abstract, we can use PDF text later
    if discipline:
        if require_abstract:
            cur.execute("""
                SELECT doi, title, abstract, discipline, journal, pdf_url
                FROM society_papers
                WHERE discipline = ? AND abstract IS NOT NULL AND abstract != ''
                ORDER BY created_at DESC
                LIMIT ?
            """, (discipline, limit))
        else:
            cur.execute("""
                SELECT doi, title, abstract, discipline, journal, pdf_url
                FROM society_papers
                WHERE discipline = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (discipline, limit))
    else:
        if require_abstract:
            cur.execute("""
                SELECT doi, title, abstract, discipline, journal, pdf_url
                FROM society_papers
                WHERE abstract IS NOT NULL AND abstract != ''
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit * 7,))
        else:
            cur.execute("""
                SELECT doi, title, abstract, discipline, journal, pdf_url
                FROM society_papers
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit * 7,))

    papers = []
    for row in cur.fetchall():
        papers.append(Paper(
            doi=row[0],
            title=row[1],
            abstract=row[2] or "",
            discipline=row[3],
            journal=row[4] or "Research Journal",
            url=row[5] or "",
            pdf_url=row[5] or None  # pdf_url same as url for now
        ))

    conn.close()
    return papers


def list_papers():
    """list all papers ready to process"""
    papers = get_papers(limit=100)

    print("\n=== PAPERS READY FOR VISUAL STORIES ===\n")

    by_discipline = {}
    for p in papers:
        if p.discipline not in by_discipline:
            by_discipline[p.discipline] = []
        by_discipline[p.discipline].append(p)

    for disc, disc_papers in sorted(by_discipline.items()):
        print(f"{disc.upper()} ({len(disc_papers)} papers):")
        for p in disc_papers[:3]:
            title = p.title[:60] + "..." if len(p.title) > 60 else p.title
            print(f"  - {title}")
        if len(disc_papers) > 3:
            print(f"  ... and {len(disc_papers) - 3} more")
        print()


def call_ollama(prompt: str) -> str:
    """call Ollama API"""
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        }, timeout=180)
        return resp.json().get("response", "")
    except Exception as e:
        print(f"  [!] ollama error: {e}")
        return ""


def generate_chapters(paper: Paper) -> List[dict]:
    """generate chapter content using LLM"""

    # use full text if available (better content), otherwise abstract
    content_source = paper.full_text if paper.full_text else paper.abstract
    content_label = "PAPER CONTENT" if paper.full_text else "ABSTRACT"

    prompt = f"""You are writing an educational article for undergraduate students about this research:

TITLE: {paper.title}
{content_label}: {content_source[:4000]}
SUBJECT: {paper.discipline}

Generate 5 chapters. For each chapter, provide:
- chapter_title: Engaging title (3-6 words)
- content: 2-3 paragraphs explaining the concept clearly for undergrads
- mermaid_code: A simple Mermaid flowchart (flowchart LR or flowchart TB) with 4-8 nodes

Output as JSON array:
[
  {{
    "chapter_title": "The Challenge",
    "content": "Paragraph 1...\\n\\nParagraph 2...",
    "mermaid_code": "flowchart LR\\n    A[Start] --> B[Process] --> C[End]"
  }}
]

Chapter flow:
1. The Challenge - What problem needs solving
2. The Approach - How researchers tackled it
3. The Innovation - What's new and different
4. The Results - What they discovered
5. Why It Matters - Future implications

Write clearly, avoid jargon. Explain like you're talking to a curious undergraduate."""

    response = call_ollama(prompt)

    # extract JSON
    try:
        match = re.search(r'\[[\s\S]*\]', response)
        if match:
            chapters = json.loads(match.group())
            if len(chapters) >= 3:
                return chapters
    except:
        pass

    # fallback chapters if LLM fails
    return [
        {"chapter_title": "The Research", "content": paper.abstract, "mermaid_code": "flowchart LR\n    A[Question] --> B[Research] --> C[Discovery]"},
        {"chapter_title": "The Method", "content": "The researchers used innovative techniques to investigate this problem.", "mermaid_code": "flowchart TB\n    A[Data] --> B[Analysis] --> C[Results]"},
        {"chapter_title": "The Impact", "content": "This work advances our understanding and opens new possibilities.", "mermaid_code": "flowchart LR\n    A[Now] --> B[Future Applications]"},
    ]


def load_curriculum():
    """load curriculum.json for course connections"""
    if CURRICULUM_PATH.exists():
        with open(CURRICULUM_PATH) as f:
            return json.load(f)
    return {}


def get_curriculum_connection(paper: Paper, curriculum: dict) -> str:
    """generate curriculum connection HTML"""

    disc_data = curriculum.get(paper.discipline, {})
    subfields = disc_data.get("subfields", {})

    if not subfields:
        # fallback generic courses
        return f'''
            <div class="course-card">
                <div class="course-code">{paper.discipline.upper()} 201</div>
                <div class="course-name">Intermediate {paper.discipline.title()}</div>
                <p class="course-connection">This research applies concepts from your coursework to real-world problems.</p>
            </div>'''

    cards_html = ""
    count = 0
    for subfield_name, subfield_data in subfields.items():
        if count >= 3:
            break

        difficulty = subfield_data.get("difficulty", "sophomore")
        level_map = {"freshman": "100", "sophomore": "200", "junior": "300"}
        level = level_map.get(difficulty, "200")

        topics = subfield_data.get("topics", [])
        topic_names = [t["name"] for t in topics[:3]]

        cards_html += f'''
            <div class="course-card">
                <div class="course-code">{paper.discipline.upper()} {level}</div>
                <div class="course-name">{subfield_name}</div>
                <p class="course-connection">This research connects to topics like {', '.join(topic_names)}.</p>
                <div class="course-concepts">
                    {''.join(f'<span class="concept-tag">{t}</span>' for t in topic_names)}
                </div>
            </div>'''
        count += 1

    return cards_html


def generate_story_html(paper: Paper, curriculum: dict) -> str:
    """generate complete story HTML for a paper (matches canonical solar-cell-bromine-story.html)"""

    print(f"  generating scenes...", end=" ", flush=True)
    chapters = generate_chapters(paper)
    print(f"{len(chapters)} scenes")

    curriculum_html = get_curriculum_connection(paper, curriculum)
    accent = COLORS.get(paper.discipline, "#10b981")

    # build scenes HTML (matching canonical template structure)
    scenes_html = ""
    total_scenes = len(chapters)
    for i, ch in enumerate(chapters, 1):
        title = ch.get("chapter_title", f"Scene {i}")
        content = ch.get("content", "")
        # wrap paragraphs properly
        paragraphs = content.split("\n\n")
        content_html = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
        mermaid = ch.get("mermaid_code", "flowchart LR\n    A --> B")

        scenes_html += f'''
        <div class="scene">
            <span class="scene-number">Scene {i} of {total_scenes}</span>
            <h2>{title}</h2>
            <div class="scene-text">
                {content_html}
            </div>
            <div class="diagram-box">
                <div class="mermaid">
{mermaid}
                </div>
            </div>
        </div>
'''

    # canonical template: matches solar-cell-bromine-story.html
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Story: {paper.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Instrument+Serif&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --accent-green: {accent};
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-orange: #f59e0b;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.7;
        }}

        .hero {{
            text-align: center;
            padding: 5rem 2rem;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-bottom: 1px solid #334155;
        }}

        .hero h1 {{
            font-family: 'Instrument Serif', serif;
            font-size: 3rem;
            color: var(--accent-green);
            margin-bottom: 1.5rem;
            font-weight: 400;
        }}

        .hero .subtitle {{
            font-size: 1.25rem;
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.8;
        }}

        .meta {{
            margin-top: 2rem;
            font-size: 0.9rem;
            color: var(--accent-cyan);
        }}

        .meta a {{
            color: var(--accent-cyan);
            text-decoration: none;
        }}

        .meta a:hover {{
            text-decoration: underline;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--accent-cyan);
            text-decoration: none;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}

        .scene {{
            margin-bottom: 4rem;
            padding-bottom: 4rem;
            border-bottom: 1px solid #334155;
        }}

        .scene:last-child {{
            border-bottom: none;
        }}

        .scene-number {{
            display: inline-block;
            background: var(--accent-green);
            color: var(--bg-dark);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}

        .scene h2 {{
            font-family: 'Instrument Serif', serif;
            color: var(--text-primary);
            font-size: 2rem;
            margin-bottom: 1.5rem;
            font-weight: 400;
        }}

        .scene-text {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }}

        .scene-text p {{
            margin-bottom: 1rem;
        }}

        .scene-text strong {{
            color: var(--text-primary);
        }}

        .diagram-box {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            overflow-x: auto;
            border: 1px solid #334155;
        }}

        .mermaid {{
            display: flex;
            justify-content: center;
        }}

        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}

        .highlight-box {{
            background: rgba(16, 185, 129, 0.1);
            border-left: 4px solid var(--accent-green);
            padding: 1.25rem 1.5rem;
            margin: 2rem 0;
            border-radius: 0 8px 8px 0;
        }}

        .highlight-box strong {{
            color: var(--accent-green);
        }}

        .curriculum-section {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            margin-top: 3rem;
            border: 1px solid #334155;
        }}

        .curriculum-header {{
            margin-bottom: 1.5rem;
        }}

        .curriculum-badge {{
            display: inline-block;
            background: var(--accent-green);
            color: var(--bg-dark);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }}

        .curriculum-title {{
            font-family: 'Instrument Serif', serif;
            font-size: 1.5rem;
            color: var(--text-primary);
            font-weight: 400;
        }}

        .course-card {{
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-left: 3px solid var(--accent-cyan);
        }}

        .course-code {{
            font-size: 0.8rem;
            color: var(--accent-cyan);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .course-name {{
            font-size: 1.1rem;
            color: var(--text-primary);
            margin: 0.25rem 0 0.75rem 0;
        }}

        .course-connection {{
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.6;
        }}

        .course-concepts {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.75rem;
        }}

        .concept-tag {{
            background: rgba(6, 182, 212, 0.1);
            border: 1px solid var(--accent-cyan);
            color: var(--accent-cyan);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
        }}

        footer {{
            text-align: center;
            padding: 3rem 2rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            border-top: 1px solid #334155;
            background: var(--bg-card);
        }}

        footer a {{
            color: var(--accent-green);
            text-decoration: none;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}

        @media (max-width: 600px) {{
            .hero h1 {{ font-size: 2rem; }}
            .scene h2 {{ font-size: 1.5rem; }}
            .container {{ padding: 2rem 1rem; }}
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>{paper.title}</h1>
        <p class="subtitle">Research explained for undergraduate students</p>
        <p class="meta">Source: {paper.journal} | <a href="{paper.url or f'https://doi.org/{paper.doi}'}">View original</a></p>
    </div>

    <div class="container">
        <a href="/{paper.discipline}.html" class="back-link">&larr; Back to {paper.discipline.title()}</a>

        {scenes_html}

        <div class="curriculum-section">
            <div class="curriculum-header">
                <span class="curriculum-badge">The Beakers</span>
                <h2 class="curriculum-title">Curriculum Connection</h2>
            </div>
            {curriculum_html}
        </div>
    </div>

    <footer>
        <p>Visual Story for <a href="https://thebeakers.com">The Beakers</a></p>
        <p style="margin-top: 0.5rem; font-size: 0.8rem;">DOI: {paper.doi}</p>
    </footer>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '{accent}',
                primaryTextColor: '#fff',
                primaryBorderColor: '{accent}',
                lineColor: '#64748b',
                secondaryColor: '#3b82f6',
                tertiaryColor: '#1e293b',
                background: '#0f172a'
            }}
        }});
    </script>
</body>
</html>'''

    return html


def slugify(title: str) -> str:
    """convert title to URL-safe slug"""
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:50]


def generate_stories(discipline: Optional[str] = None, count: int = 2, verbose: bool = True, use_pdfs: bool = True):
    """generate visual stories for papers

    if use_pdfs=True, will download and extract PDF text for papers without abstracts
    """

    # get all papers (not just those with abstracts) if using PDFs
    papers = get_papers(discipline, limit=count, require_abstract=not use_pdfs)

    if not papers:
        print("[!] no papers found to process")
        return

    curriculum = load_curriculum()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    skipped_no_content = []

    for paper in papers:
        if verbose:
            print(f"\n[{paper.discipline.upper()}] {paper.title[:60]}...")

        # check if already exists
        slug = slugify(paper.title)
        output_file = OUTPUT_DIR / f"{slug}-story.html"

        if output_file.exists():
            if verbose:
                print(f"  skipping (already exists)")
            continue

        # if no abstract, try to get PDF text
        if not paper.abstract and use_pdfs:
            if verbose:
                print(f"  no abstract, trying PDF...")
            pdf_path = download_pdf(paper)
            if pdf_path:
                paper.full_text = extract_pdf_text(pdf_path)
                if paper.full_text:
                    if verbose:
                        print(f"  extracted {len(paper.full_text)} chars from PDF")
                else:
                    if verbose:
                        print(f"  [!] could not extract text from PDF")

            # skip if still no content
            if not paper.abstract and not paper.full_text:
                if verbose:
                    print(f"  [!] skipping - no abstract or PDF text available")
                skipped_no_content.append(paper.title)
                continue

        try:
            html = generate_story_html(paper, curriculum)
            output_file.write_text(html)
            generated.append({
                "discipline": paper.discipline,
                "title": paper.title,
                "file": str(output_file.name)
            })
            if verbose:
                print(f"  saved: {output_file.name}")
        except Exception as e:
            if verbose:
                print(f"  [!] error: {e}")

    print(f"\n=== GENERATED {len(generated)} VISUAL STORIES ===")
    for g in generated:
        print(f"  [{g['discipline']}] {g['file']}")

    if skipped_no_content:
        print(f"\n=== SKIPPED {len(skipped_no_content)} (no content) ===")
        for title in skipped_no_content[:5]:
            print(f"  - {title[:50]}...")


def main():
    parser = argparse.ArgumentParser(description="Generate visual stories from collected papers")
    parser.add_argument("discipline", nargs="?", help="Discipline to generate for")
    parser.add_argument("--list", action="store_true", help="List papers ready to process")
    parser.add_argument("--count", type=int, default=2, help="Stories per discipline (default: 2)")
    parser.add_argument("--no-pdf", action="store_true", help="Don't try to download PDFs (abstract only)")
    args = parser.parse_args()

    if args.list:
        list_papers()
        return

    generate_stories(args.discipline, args.count, use_pdfs=not args.no_pdf)


if __name__ == "__main__":
    main()
