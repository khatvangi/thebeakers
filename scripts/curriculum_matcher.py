#!/usr/bin/env python3
"""
curriculum_matcher.py - match papers to curriculum topics via Qdrant

queries qdrant chunks_text for LibreTexts content similar to a paper,
identifies relevant curriculum topics, and generates curriculum connection HTML.

usage:
    python curriculum_matcher.py --doi "10.1021/xxx"      # match from database
    python curriculum_matcher.py --title "Paper title" --abstract "Abstract text" --discipline chemistry
    python curriculum_matcher.py --test                   # test with sample paper
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from qdrant_client import QdrantClient

# paths
SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
CURRICULUM_PATH = PROJECT_DIR / "data" / "curriculum.json"
DB_PATH = PROJECT_DIR / "data" / "articles.db"

# qdrant config
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
CHUNKS_COLLECTION = "chunks_text"

# ollama config
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text:latest"
EMBED_DIM = 768

# matching config
TOP_K_CHUNKS = 10
MIN_SCORE_THRESHOLD = 0.5


def load_curriculum() -> Dict:
    """load curriculum.json"""
    if not CURRICULUM_PATH.exists():
        print(f"[!] curriculum.json not found at {CURRICULUM_PATH}")
        return {}
    with open(CURRICULUM_PATH) as f:
        return json.load(f)


def get_qdrant_client() -> QdrantClient:
    """get qdrant client"""
    return QdrantClient(url=QDRANT_URL)


def get_embedding(text: str) -> List[float]:
    """get embedding for text using Ollama"""
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding", [0.0] * EMBED_DIM)
    except Exception as e:
        print(f"[!] embedding error: {e}")
        return [0.0] * EMBED_DIM


def query_qdrant_for_paper(client: QdrantClient, title: str, abstract: str, k: int = TOP_K_CHUNKS) -> List[Dict]:
    """query qdrant chunks_text for paper content"""

    # combine title and abstract for query
    query_text = f"{title}\n\n{abstract}"
    query_vec = get_embedding(query_text)

    try:
        results = client.query_points(
            collection_name=CHUNKS_COLLECTION,
            query=query_vec,
            limit=k,
            with_payload=True,
        )
        return [
            {
                "text": r.payload.get("text", ""),
                "pdf_name": r.payload.get("pdf_name", ""),
                "chunk_id": r.payload.get("chunk_id", 0),
                "score": r.score,
            }
            for r in results.points
            if r.score >= MIN_SCORE_THRESHOLD
        ]
    except Exception as e:
        print(f"[!] qdrant search error: {e}")
        return []


def extract_libretexts_category(pdf_name: str) -> Tuple[str, str]:
    """extract discipline and category from LibreTexts PDF name"""

    # common mappings from PDF names to categories
    category_patterns = {
        # chemistry
        "general_chemistry": ("chemistry", "General Chemistry"),
        "organic_chemistry": ("chemistry", "Organic Chemistry"),
        "physical_chemistry": ("chemistry", "Physical Chemistry"),
        "analytical_chemistry": ("chemistry", "Analytical Chemistry"),
        "inorganic_chemistry": ("chemistry", "Inorganic Chemistry"),
        "introductory_chemistry": ("chemistry", "General Chemistry"),
        "gob_chemistry": ("chemistry", "General Chemistry"),  # GOB = General, Organic, Biochemistry

        # physics
        "university_physics": ("physics", "Classical Mechanics"),
        "classical_mechanics": ("physics", "Classical Mechanics"),
        "quantum_mechanics": ("physics", "Quantum Mechanics"),
        "electromagnetism": ("physics", "Electromagnetism"),
        "thermodynamics": ("physics", "Thermodynamics"),
        "optics": ("physics", "Optics"),

        # biology
        "molecular_biology": ("biology", "Molecular Biology"),
        "cell_biology": ("biology", "Cell Biology"),
        "genetics": ("biology", "Genetics"),
        "biochemistry": ("biology", "Biochemistry"),
        "ecology": ("biology", "Ecology"),

        # mathematics
        "calculus": ("mathematics", "Calculus"),
        "linear_algebra": ("mathematics", "Linear Algebra"),
        "differential_equations": ("mathematics", "Differential Equations"),
        "probability": ("mathematics", "Probability & Statistics"),
        "statistics": ("mathematics", "Probability & Statistics"),
        "discrete": ("mathematics", "Discrete Mathematics"),

        # engineering
        "statics": ("engineering", "Mechanical Engineering"),
        "dynamics": ("engineering", "Mechanical Engineering"),
        "circuits": ("engineering", "Electrical Engineering"),
        "materials": ("engineering", "Civil Engineering"),
        "thermodynamics": ("engineering", "Chemical Engineering"),
    }

    pdf_lower = pdf_name.lower()

    for pattern, (discipline, category) in category_patterns.items():
        if pattern in pdf_lower:
            return discipline, category

    return "unknown", "unknown"


def identify_difficulty_level(chunks: List[Dict], curriculum: Dict, discipline: str) -> Tuple[str, str]:
    """identify difficulty level from matched chunks"""

    if not chunks or discipline not in curriculum:
        return "sophomore", "200-300"  # default

    # count category matches
    category_counts = {}
    for chunk in chunks:
        _, category = extract_libretexts_category(chunk["pdf_name"])
        category_counts[category] = category_counts.get(category, 0) + 1

    # find most common category
    if not category_counts:
        return "sophomore", "200-300"

    top_category = max(category_counts, key=category_counts.get)

    # look up in curriculum
    disc_data = curriculum.get(discipline, {})
    for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
        if subfield_name.lower() == top_category.lower():
            difficulty = subfield_data.get("difficulty", "sophomore")
            level = subfield_data.get("level", "200-300")
            return difficulty, level

    return "sophomore", "200-300"


def match_curriculum_topics(title: str, abstract: str, discipline: str, curriculum: Dict) -> List[Dict]:
    """match paper to curriculum topics based on keywords"""

    if discipline not in curriculum:
        return []

    text = f"{title} {abstract}".lower()
    matched_topics = []

    for subfield_name, subfield_data in curriculum[discipline].get("subfields", {}).items():
        for topic in subfield_data.get("topics", []):
            topic_name = topic["name"]
            keywords = topic.get("keywords", [])

            # count keyword matches
            match_count = 0
            matched_keywords = []
            for keyword in keywords:
                if keyword.lower() in text:
                    match_count += 1
                    matched_keywords.append(keyword)

            if match_count > 0:
                matched_topics.append({
                    "topic": topic_name,
                    "subfield": subfield_name,
                    "keywords": matched_keywords,
                    "match_count": match_count,
                    "difficulty": subfield_data.get("difficulty", "sophomore"),
                    "level": subfield_data.get("level", "200-300"),
                })

    # sort by match count
    matched_topics.sort(key=lambda x: x["match_count"], reverse=True)
    return matched_topics[:5]


def generate_curriculum_connection(
    title: str,
    abstract: str,
    discipline: str,
    chunks: List[Dict],
    matched_topics: List[Dict],
    difficulty: str,
    level: str
) -> Dict:
    """generate curriculum connection data"""

    # determine overall difficulty
    difficulty_display = {
        "freshman": "Freshman (100-200 level)",
        "sophomore": "Sophomore (200-300 level)",
        "junior": "Junior (300+ level)",
    }.get(difficulty, "Undergraduate")

    # extract prerequisite concepts from lower-level matches
    prerequisites = []
    for topic in matched_topics:
        if topic["difficulty"] in ["freshman"] and difficulty != "freshman":
            prerequisites.append(f"{topic['subfield']}: {topic['topic']}")

    # extract related topics from same-level matches
    related = []
    for topic in matched_topics:
        if topic["difficulty"] == difficulty:
            related.append(f"{topic['subfield']}: {topic['topic']}")

    # extract advanced topics from higher-level matches
    advanced = []
    for topic in matched_topics:
        if topic["difficulty"] == "junior" and difficulty != "junior":
            advanced.append(f"{topic['subfield']}: {topic['topic']}")

    # source textbooks
    sources = list(set([
        chunk["pdf_name"].replace(".pdf", "").replace("_", " ").title()
        for chunk in chunks[:3]
    ]))

    return {
        "difficulty": difficulty,
        "difficulty_display": difficulty_display,
        "level": level,
        "prerequisites": prerequisites[:3],
        "related_topics": related[:4],
        "advanced_topics": advanced[:2],
        "matched_topics": matched_topics,
        "sources": sources,
    }


def generate_html_section(connection: Dict, discipline: str) -> str:
    """generate HTML for curriculum connection section"""

    difficulty_class = {
        "freshman": "freshman",
        "sophomore": "sophomore",
        "junior": "junior",
    }.get(connection["difficulty"], "sophomore")

    html = f'''
<section class="curriculum-connection">
    <h3>Curriculum Connection</h3>
    <div class="level-badge {difficulty_class}">{connection["difficulty_display"]}</div>

    <div class="curriculum-grid">
'''

    if connection["related_topics"]:
        html += '''        <div class="curriculum-item">
            <h4>Related Topics</h4>
            <ul>
'''
        for topic in connection["related_topics"]:
            html += f'                <li>{topic}</li>\n'
        html += '''            </ul>
        </div>
'''

    if connection["prerequisites"]:
        html += '''        <div class="curriculum-item">
            <h4>Prerequisites</h4>
            <ul>
'''
        for topic in connection["prerequisites"]:
            html += f'                <li>{topic}</li>\n'
        html += '''            </ul>
        </div>
'''

    if connection["advanced_topics"]:
        html += '''        <div class="curriculum-item">
            <h4>Advanced Topics</h4>
            <ul>
'''
        for topic in connection["advanced_topics"]:
            html += f'                <li>{topic}</li>\n'
        html += '''            </ul>
        </div>
'''

    if connection["sources"]:
        html += '''        <div class="curriculum-item sources">
            <h4>Reference Texts</h4>
            <ul>
'''
        for source in connection["sources"]:
            html += f'                <li>{source}</li>\n'
        html += '''            </ul>
        </div>
'''

    html += '''    </div>
</section>
'''

    return html


def match_paper(title: str, abstract: str, discipline: str) -> Dict:
    """main matching function"""

    client = get_qdrant_client()
    curriculum = load_curriculum()

    # query qdrant for relevant chunks
    chunks = query_qdrant_for_paper(client, title, abstract)

    # identify difficulty level
    difficulty, level = identify_difficulty_level(chunks, curriculum, discipline)

    # match curriculum topics
    matched_topics = match_curriculum_topics(title, abstract, discipline, curriculum)

    # generate connection
    connection = generate_curriculum_connection(
        title, abstract, discipline, chunks, matched_topics, difficulty, level
    )

    # generate HTML
    html = generate_html_section(connection, discipline)

    return {
        "connection": connection,
        "html": html,
        "chunks": chunks[:5],  # top 5 for reference
    }


def get_paper_from_db(doi: str) -> Optional[Dict]:
    """get paper from society_papers database"""

    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT title, abstract, discipline FROM society_papers WHERE doi = ?
    """, (doi,))

    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "title": row[0],
            "abstract": row[1] or "",
            "discipline": row[2],
        }
    return None


def main():
    parser = argparse.ArgumentParser(description="Match papers to curriculum topics")
    parser.add_argument("--doi", help="Paper DOI to match from database")
    parser.add_argument("--title", help="Paper title")
    parser.add_argument("--abstract", help="Paper abstract")
    parser.add_argument("--discipline", help="Discipline (chemistry, physics, etc.)")
    parser.add_argument("--test", action="store_true", help="Test with sample paper")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.test:
        # test with a sample kinetics paper
        title = "Catalyst Design for Enhanced Reaction Rates in SN2 Substitution"
        abstract = """We report a novel approach to accelerating nucleophilic substitution
        reactions through precise catalyst design. By optimizing the transition state
        stabilization and reducing activation energy barriers, we achieved significant
        rate enhancements. The Arrhenius parameters were determined across multiple
        substrates, revealing insights into the reaction mechanism and stereochemistry."""
        discipline = "chemistry"
    elif args.doi:
        paper = get_paper_from_db(args.doi)
        if not paper:
            print(f"[!] paper not found: {args.doi}")
            return
        title = paper["title"]
        abstract = paper["abstract"]
        discipline = paper["discipline"]
    elif args.title and args.discipline:
        title = args.title
        abstract = args.abstract or ""
        discipline = args.discipline
    else:
        parser.print_help()
        return

    print(f"\n=== CURRICULUM MATCHING ===")
    print(f"Title: {title[:80]}...")
    print(f"Discipline: {discipline}")

    result = match_paper(title, abstract, discipline)

    if args.json:
        print(json.dumps(result["connection"], indent=2))
    else:
        print(f"\n=== CONNECTION ===")
        print(f"Difficulty: {result['connection']['difficulty_display']}")
        print(f"Level: {result['connection']['level']}")

        if result['connection']['related_topics']:
            print(f"\nRelated Topics:")
            for t in result['connection']['related_topics']:
                print(f"  - {t}")

        if result['connection']['prerequisites']:
            print(f"\nPrerequisites:")
            for t in result['connection']['prerequisites']:
                print(f"  - {t}")

        if result['connection']['sources']:
            print(f"\nReference Texts:")
            for s in result['connection']['sources']:
                print(f"  - {s}")

        print(f"\n=== HTML OUTPUT ===")
        print(result['html'])


if __name__ == "__main__":
    main()
