#!/usr/bin/env python3
"""
batch_visual_stories.py - generate visual stories for all subfields

pipeline:
1. read curriculum.json for subfields + keywords
2. query OpenAlex for 3 papers per subfield (open access)
3. select format: visual (data-heavy) or story (mechanism)
4. generate content with Qwen + Gemma counsel
5. create HTML using locked templates

usage:
    python scripts/batch_visual_stories.py --discipline chemistry
    python scripts/batch_visual_stories.py --all
    python scripts/batch_visual_stories.py --all --dry-run
"""

import argparse
import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# paths
BASE_DIR = Path(__file__).parent.parent
CURRICULUM_PATH = BASE_DIR / "data" / "curriculum.json"
OUTPUT_DIR = BASE_DIR / "explain"
TEMPLATE_VISUAL = BASE_DIR / "deepdive" / "solar-cell-bromine-visual.html"
TEMPLATE_STORY = BASE_DIR / "deepdive" / "solar-cell-bromine-story.html"

# openalex config
OPENALEX_EMAIL = "thebeakerscom@gmail.com"
HEADERS = {"User-Agent": f"TheBeakers/1.0 (mailto:{OPENALEX_EMAIL})"}

# ollama config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_QWEN = "qwen3:latest"
MODEL_GEMMA = "gemma2:9b"


def load_curriculum() -> Dict:
    """load curriculum.json"""
    with open(CURRICULUM_PATH) as f:
        return json.load(f)


def search_openalex(keywords: List[str], discipline: str, limit: int = 5) -> List[Dict]:
    """search OpenAlex for papers matching keywords"""
    # build query from keywords
    query = " OR ".join(keywords[:5])  # limit keywords to avoid too broad
    from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    params = {
        "mailto": OPENALEX_EMAIL,
        "search": query,
        "filter": f"from_publication_date:{from_date},is_oa:true",
        "per_page": limit,
        "sort": "cited_by_count:desc",
    }

    try:
        resp = requests.get(
            "https://api.openalex.org/works",
            params=params,
            headers=HEADERS,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for work in data.get("results", []):
            doi = work.get("doi", "").replace("https://doi.org/", "")
            if not doi:
                continue

            # get abstract - openalex returns inverted index
            abstract = ""
            if work.get("abstract_inverted_index"):
                # reconstruct abstract from inverted index
                inv_idx = work["abstract_inverted_index"]
                word_positions = []
                for word, positions in inv_idx.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join(w for _, w in word_positions)

            # safely get source name
            primary_loc = work.get("primary_location") or {}
            source_info = primary_loc.get("source") or {}
            source_name = source_info.get("display_name", "OpenAlex")

            papers.append({
                "doi": doi,
                "title": work.get("title", ""),
                "abstract": abstract[:2000],
                "source": source_name,
                "published_date": work.get("publication_date", ""),
                "cited_by_count": work.get("cited_by_count", 0),
                "discipline": discipline,
            })

        return papers

    except Exception as e:
        print(f"  OpenAlex error: {e}")
        return []


def select_format(paper: Dict) -> str:
    """determine if paper should use visual or story format"""
    abstract = paper.get("abstract", "").lower()
    title = paper.get("title", "").lower()
    combined = f"{title} {abstract}"

    # visual indicators: numbers, comparisons, data
    visual_keywords = [
        "compared", "comparison", "versus", "vs", "percent", "%",
        "increased", "decreased", "efficiency", "performance",
        "measured", "quantified", "results show", "data",
        "statistical", "significant", "improvement"
    ]

    # story indicators: mechanisms, processes, theory
    story_keywords = [
        "mechanism", "pathway", "process", "how", "why",
        "hypothesis", "theory", "model", "explains",
        "step", "stage", "phase", "cascade", "signaling"
    ]

    visual_score = sum(1 for kw in visual_keywords if kw in combined)
    story_score = sum(1 for kw in story_keywords if kw in combined)

    return "visual" if visual_score >= story_score else "story"


def query_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    """query ollama model"""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 2000}
            },
            timeout=timeout
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"  Ollama error ({model}): {e}")
        return ""


def counsel_generate(paper: Dict, format_type: str) -> Dict:
    """
    generate content using Qwen + Gemma counsel
    both models generate, then we merge the best parts
    """
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    discipline = paper.get("discipline", "")

    if format_type == "visual":
        prompt = f"""You are writing a visual summary for undergraduate students.

Paper: {title}
Discipline: {discipline}
Abstract: {abstract}

Generate a JSON object with these fields:
{{
    "headline": "catchy headline (max 10 words)",
    "subtitle": "one sentence explaining the finding",
    "hero_stats": [
        {{"value": "X%", "label": "what it measures"}},
        {{"value": "Nx", "label": "improvement factor"}},
        {{"value": "N", "label": "samples/subjects"}}
    ],
    "challenge": "what problem does this solve? (2 sentences)",
    "method": "how did they do it? (2 sentences)",
    "result": "what did they find? (2 sentences)",
    "insight": "why does this matter for students? (1 sentence)",
    "curriculum_connection": "which undergraduate course covers this topic"
}}

Return ONLY valid JSON, no markdown or explanation."""
    else:
        prompt = f"""You are writing a story-based explanation for undergraduate students.

Paper: {title}
Discipline: {discipline}
Abstract: {abstract}

Generate a JSON object with these fields:
{{
    "headline": "intriguing headline (max 10 words)",
    "subtitle": "the big question this research answers",
    "scenes": [
        {{"title": "The Challenge", "content": "what problem exists (2-3 sentences)", "diagram_type": "mindmap"}},
        {{"title": "The Hypothesis", "content": "what did researchers propose (2-3 sentences)", "diagram_type": "flowchart"}},
        {{"title": "The Method", "content": "how they tested it (2-3 sentences)", "diagram_type": "flowchart"}},
        {{"title": "The Discovery", "content": "what they found (2-3 sentences)", "diagram_type": "flowchart"}},
        {{"title": "Why It Matters", "content": "implications for the field (2-3 sentences)", "diagram_type": "mindmap"}}
    ],
    "key_insight": "one takeaway for students",
    "curriculum_connection": "which undergraduate course covers this topic"
}}

Return ONLY valid JSON, no markdown or explanation."""

    # query both models
    print(f"    Querying {MODEL_QWEN}...")
    qwen_response = query_ollama(MODEL_QWEN, prompt)

    print(f"    Querying {MODEL_GEMMA}...")
    gemma_response = query_ollama(MODEL_GEMMA, prompt)

    # parse responses
    def extract_json(text: str) -> Optional[Dict]:
        # try to find JSON in response
        text = text.strip()
        # remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        try:
            return json.loads(text)
        except:
            # try to find JSON object
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
        return None

    qwen_data = extract_json(qwen_response)
    gemma_data = extract_json(gemma_response)

    # counsel: merge best parts
    if qwen_data and gemma_data:
        # prefer qwen for structure, gemma for prose
        result = qwen_data.copy()
        if len(gemma_data.get("subtitle", "")) > len(qwen_data.get("subtitle", "")):
            result["subtitle"] = gemma_data["subtitle"]
        if gemma_data.get("key_insight"):
            result["key_insight"] = gemma_data["key_insight"]
        return result

    return qwen_data or gemma_data or {}


def generate_visual_html(paper: Dict, content: Dict) -> str:
    """generate visual format HTML"""
    headline = content.get("headline", paper.get("title", "")[:50])
    subtitle = content.get("subtitle", "")
    stats = content.get("hero_stats", [])
    challenge = content.get("challenge", "")
    method = content.get("method", "")
    result = content.get("result", "")
    insight = content.get("insight", "")
    curriculum = content.get("curriculum_connection", "")

    # build stats HTML
    stats_html = ""
    for stat in stats[:3]:
        stats_html += f'''
            <div class="hero-stat">
                <div class="value">{stat.get("value", "")}</div>
                <div class="label">{stat.get("label", "")}</div>
            </div>'''

    doi = paper.get("doi", "")
    source = paper.get("source", "")
    discipline = paper.get("discipline", "")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline} — The Beakers</title>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Instrument+Serif&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --accent-green: #10b981;
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
            line-height: 1.6;
        }}
        .hero {{
            background: linear-gradient(135deg, #064e3b 0%, #0f172a 50%, #1e1b4b 100%);
            padding: 4rem 2rem;
            text-align: center;
        }}
        .hero h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, var(--accent-green), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }}
        .hero .subtitle {{
            font-size: 1.2rem;
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 auto 2rem;
        }}
        .hero-stats {{
            display: flex;
            justify-content: center;
            gap: 3rem;
            flex-wrap: wrap;
        }}
        .hero-stat {{ text-align: center; }}
        .hero-stat .value {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--accent-orange);
        }}
        .hero-stat .label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
        .section {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        .section h2 {{
            font-size: 1.5rem;
            color: var(--accent-green);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .section p {{ color: var(--text-secondary); line-height: 1.8; }}
        .insight-box {{
            background: linear-gradient(135deg, #064e3b, #0f172a);
            border-left: 4px solid var(--accent-green);
            padding: 1.5rem;
            border-radius: 8px;
            margin-top: 2rem;
        }}
        .insight-box h3 {{ color: var(--accent-green); margin-bottom: 0.5rem; }}
        .meta {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .meta a {{ color: var(--accent-cyan); text-decoration: none; }}
        .meta a:hover {{ text-decoration: underline; }}
        .curriculum {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 2rem;
            border: 1px solid #334155;
        }}
        .curriculum h3 {{
            color: var(--accent-cyan);
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }}
        .curriculum p {{ color: var(--text-secondary); font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>{headline}</h1>
        <p class="subtitle">{subtitle}</p>
        <div class="hero-stats">{stats_html}
        </div>
    </div>

    <div class="container">
        <div class="section">
            <h2><i data-lucide="alert-triangle"></i> The Challenge</h2>
            <p>{challenge}</p>
        </div>

        <div class="section">
            <h2><i data-lucide="flask-conical"></i> The Method</h2>
            <p>{method}</p>
        </div>

        <div class="section">
            <h2><i data-lucide="sparkles"></i> The Discovery</h2>
            <p>{result}</p>
        </div>

        <div class="insight-box">
            <h3>💡 Key Insight</h3>
            <p>{insight}</p>
        </div>

        <div class="curriculum">
            <h3>📚 Curriculum Connection</h3>
            <p>{curriculum}</p>
        </div>

        <div class="meta">
            <p>Source: <a href="https://doi.org/{doi}" target="_blank">{source}</a> | {discipline.title()}</p>
            <p style="margin-top: 0.5rem;">Generated by The Beakers</p>
        </div>
    </div>

    <script>lucide.createIcons();</script>
</body>
</html>'''


def generate_story_html(paper: Dict, content: Dict) -> str:
    """generate story format HTML with mermaid diagrams"""
    headline = content.get("headline", paper.get("title", "")[:50])
    subtitle = content.get("subtitle", "")
    scenes = content.get("scenes", [])
    insight = content.get("key_insight", "")
    curriculum = content.get("curriculum_connection", "")

    doi = paper.get("doi", "")
    source = paper.get("source", "")
    discipline = paper.get("discipline", "")

    # build scenes HTML
    scenes_html = ""
    for i, scene in enumerate(scenes, 1):
        title = scene.get("title", f"Scene {i}")
        content_text = scene.get("content", "")
        diagram_type = scene.get("diagram_type", "flowchart")

        # generate simple mermaid diagram based on scene
        if diagram_type == "mindmap":
            mermaid_code = f'''mindmap
  root(({title}))
    Key Point 1
    Key Point 2
    Key Point 3'''
        else:
            mermaid_code = f'''flowchart LR
    A[Start] --> B[Process]
    B --> C[Result]'''

        scenes_html += f'''
        <div class="scene">
            <span class="scene-number">Scene {i}</span>
            <h2>{title}</h2>
            <p>{content_text}</p>
            <div class="mermaid">{mermaid_code}</div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline} — The Beakers</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Instrument+Serif&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --accent-green: #10b981;
            --accent-cyan: #06b6d4;
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
            font-size: 2.8rem;
            color: var(--accent-green);
            margin-bottom: 1.5rem;
            font-weight: 400;
        }}
        .hero .subtitle {{
            font-size: 1.2rem;
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 auto;
        }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 3rem 2rem; }}
        .scene {{
            margin-bottom: 4rem;
            padding-bottom: 3rem;
            border-bottom: 1px solid #334155;
        }}
        .scene:last-child {{ border-bottom: none; }}
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
            font-size: 2rem;
            margin-bottom: 1.5rem;
            font-weight: 400;
        }}
        .scene p {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }}
        .mermaid {{
            background: var(--bg-card);
            padding: 2rem;
            border-radius: 12px;
            margin-top: 1.5rem;
        }}
        .insight-box {{
            background: linear-gradient(135deg, #064e3b, #0f172a);
            border-left: 4px solid var(--accent-green);
            padding: 2rem;
            border-radius: 8px;
            margin: 3rem 0;
        }}
        .insight-box h3 {{ color: var(--accent-green); margin-bottom: 0.5rem; }}
        .insight-box p {{ color: var(--text-primary); font-size: 1.1rem; }}
        .curriculum {{
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #334155;
        }}
        .curriculum h3 {{ color: var(--accent-cyan); margin-bottom: 0.5rem; }}
        .curriculum p {{ color: var(--text-secondary); }}
        .meta {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .meta a {{ color: var(--accent-cyan); text-decoration: none; }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>{headline}</h1>
        <p class="subtitle">{subtitle}</p>
        <p class="meta" style="margin-top: 2rem;">
            <a href="https://doi.org/{doi}" target="_blank">{source}</a>
        </p>
    </div>

    <div class="container">
        {scenes_html}

        <div class="insight-box">
            <h3>💡 Key Takeaway</h3>
            <p>{insight}</p>
        </div>

        <div class="curriculum">
            <h3>📚 Curriculum Connection</h3>
            <p>{curriculum}</p>
        </div>

        <div class="meta">
            <p>Generated by The Beakers | {discipline.title()}</p>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#10b981',
                primaryTextColor: '#e2e8f0',
                primaryBorderColor: '#334155',
                lineColor: '#64748b',
                secondaryColor: '#1e293b',
                tertiaryColor: '#0f172a'
            }}
        }});
    </script>
</body>
</html>'''


def slugify(text: str) -> str:
    """convert text to URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:50].strip('-')


def process_subfield(
    discipline: str,
    subfield: str,
    subfield_data: Dict,
    dry_run: bool = False
) -> List[str]:
    """process one subfield: fetch papers, generate stories"""
    topics = subfield_data.get("topics", [])

    # collect all keywords from topics
    keywords = []
    for topic in topics:
        keywords.extend(topic.get("keywords", []))
        keywords.append(topic.get("name", ""))

    # dedupe and limit
    keywords = list(set(keywords))[:10]

    print(f"\n  [{subfield}] keywords: {', '.join(keywords[:5])}...")

    # fetch papers
    papers = search_openalex(keywords, discipline, limit=5)

    if not papers:
        print(f"    No papers found")
        return []

    print(f"    Found {len(papers)} papers")

    generated = []
    for i, paper in enumerate(papers[:3]):  # max 3 per subfield
        title = paper.get("title", "")[:60]
        print(f"    [{i+1}] {title}...")

        # select format
        fmt = select_format(paper)
        print(f"        Format: {fmt}")

        if dry_run:
            generated.append(f"{discipline}-{slugify(subfield)}-{i+1}.html")
            continue

        # generate content with counsel
        print(f"        Generating content...")
        content = counsel_generate(paper, fmt)

        if not content:
            print(f"        Failed to generate content")
            continue

        # generate HTML
        if fmt == "visual":
            html = generate_visual_html(paper, content)
        else:
            html = generate_story_html(paper, content)

        # save
        filename = f"{discipline}-{slugify(subfield)}-{slugify(title)}.html"
        filepath = OUTPUT_DIR / filename

        OUTPUT_DIR.mkdir(exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(html)

        print(f"        Saved: {filename}")
        generated.append(filename)

        # rate limit
        time.sleep(1)

    return generated


def main():
    parser = argparse.ArgumentParser(description="generate visual stories for subfields")
    parser.add_argument("--discipline", help="single discipline to process")
    parser.add_argument("--all", action="store_true", help="process all disciplines")
    parser.add_argument("--dry-run", action="store_true", help="don't generate, just show plan")
    parser.add_argument("--subfield", help="single subfield to process")

    args = parser.parse_args()

    curriculum = load_curriculum()

    # filter disciplines
    disciplines = list(curriculum.keys())
    disciplines = [d for d in disciplines if not d.startswith("_")]

    if args.discipline:
        disciplines = [args.discipline]
    elif not args.all:
        print("Specify --discipline or --all")
        return

    total_generated = []

    for discipline in disciplines:
        disc_data = curriculum.get(discipline, {})
        subfields = disc_data.get("subfields", {})

        print(f"\n{'='*60}")
        print(f"DISCIPLINE: {discipline.upper()}")
        print(f"{'='*60}")

        for subfield_name, subfield_data in subfields.items():
            if args.subfield and args.subfield.lower() != subfield_name.lower():
                continue

            generated = process_subfield(
                discipline,
                subfield_name,
                subfield_data,
                dry_run=args.dry_run
            )
            total_generated.extend(generated)

    print(f"\n{'='*60}")
    print(f"SUMMARY: Generated {len(total_generated)} articles")
    print(f"{'='*60}")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually created")


if __name__ == "__main__":
    main()
