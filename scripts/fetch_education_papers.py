#!/usr/bin/env python3
"""
fetch_education_papers.py - collect papers from education journals

focuses on:
- teaching methods
- common misconceptions
- hands-on experiments
- visualization strategies

sources:
- Journal of Chemical Education
- The Physics Teacher
- American Biology Teacher
- CBE Life Sciences Education
- PRIMUS (math education)
- Computer Science Education
"""

import argparse
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# config
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "education_papers"
OPENALEX_EMAIL = "thebeakerscom@gmail.com"
HEADERS = {"User-Agent": f"TheBeakers/1.0 (mailto:{OPENALEX_EMAIL})"}

# education journal ISSNs/sources
EDUCATION_SOURCES = {
    "chemistry": [
        "Journal of Chemical Education",
        "Chemistry Education Research and Practice",
    ],
    "physics": [
        "The Physics Teacher",
        "American Journal of Physics",
        "Physics Education",
    ],
    "biology": [
        "The American Biology Teacher",
        "CBE Life Sciences Education",
        "Journal of Biological Education",
    ],
    "mathematics": [
        "PRIMUS",
        "International Journal of Mathematical Education",
        "Mathematics Teacher",
    ],
    "engineering": [
        "Journal of Engineering Education",
        "IEEE Transactions on Education",
    ],
    "ai": [
        "Computer Science Education",
        "ACM Transactions on Computing Education",
    ],
    "agriculture": [
        "Journal of Agricultural Education",
        "NACTA Journal",
    ],
}

# education-specific keywords
EDUCATION_KEYWORDS = [
    "misconception",
    "students struggle",
    "hands-on",
    "demonstration",
    "visualization",
    "active learning",
    "inquiry-based",
    "conceptual understanding",
    "teaching strategy",
    "pedagogy",
    "classroom",
    "undergraduate",
    "introductory course",
]


def search_education_papers(
    discipline: str,
    limit: int = 20,
    days: int = 180
) -> List[Dict]:
    """search for education papers in a discipline"""

    sources = EDUCATION_SOURCES.get(discipline, [])
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # search by education keywords + discipline
    keywords = " OR ".join([f'"{kw}"' for kw in EDUCATION_KEYWORDS[:5]])
    query = f"({keywords}) {discipline}"

    params = {
        "mailto": OPENALEX_EMAIL,
        "search": query,
        "filter": f"from_publication_date:{from_date},is_oa:true",
        "per_page": min(limit, 100),
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

            # reconstruct abstract
            abstract = ""
            if work.get("abstract_inverted_index"):
                inv_idx = work["abstract_inverted_index"]
                word_positions = []
                for word, positions in inv_idx.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join(w for _, w in word_positions)

            # get source safely
            primary_loc = work.get("primary_location") or {}
            source_info = primary_loc.get("source") or {}
            source_name = source_info.get("display_name", "")

            # categorize education type
            edu_type = categorize_education_type(work.get("title", ""), abstract)

            papers.append({
                "doi": doi,
                "title": work.get("title", ""),
                "abstract": abstract[:2000],
                "source": source_name,
                "published_date": work.get("publication_date", ""),
                "cited_by_count": work.get("cited_by_count", 0),
                "discipline": discipline,
                "education_type": edu_type,
                "url": f"https://doi.org/{doi}",
            })

        return papers

    except Exception as e:
        print(f"  Error: {e}")
        return []


def categorize_education_type(title: str, abstract: str) -> str:
    """categorize the type of education paper"""
    combined = f"{title} {abstract}".lower()

    if any(kw in combined for kw in ["misconception", "students struggle", "common error"]):
        return "misconception"
    elif any(kw in combined for kw in ["hands-on", "experiment", "lab", "demonstration"]):
        return "experiment"
    elif any(kw in combined for kw in ["visualization", "animation", "simulation"]):
        return "visualization"
    elif any(kw in combined for kw in ["active learning", "inquiry", "problem-based"]):
        return "teaching_method"
    else:
        return "general"


def extract_visualization_concept(paper: Dict) -> Dict:
    """extract key concept for Salvador visualization"""
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    discipline = paper.get("discipline", "")
    edu_type = paper.get("education_type", "")

    return {
        "paper_doi": paper.get("doi", ""),
        "paper_title": title,
        "discipline": discipline,
        "education_type": edu_type,
        "concept_summary": abstract[:500],
        "visualization_prompt": f"""
Visualize this educational concept from a {discipline} education paper:

Title: {title}

Key points from abstract:
{abstract[:800]}

Education type: {edu_type}

Create a p5.js visualization that:
1. Shows the concept progressively (stages)
2. Highlights what students typically misunderstand
3. Uses clear labels and data cards
4. Has continuous motion to keep engagement
""".strip(),
    }


def main():
    parser = argparse.ArgumentParser(description="fetch education papers")
    parser.add_argument("--discipline", help="single discipline")
    parser.add_argument("--all", action="store_true", help="all disciplines")
    parser.add_argument("--limit", type=int, default=10, help="papers per discipline")
    parser.add_argument("--days", type=int, default=180, help="papers from last N days")
    parser.add_argument("--output", help="output JSON file")

    args = parser.parse_args()

    disciplines = list(EDUCATION_SOURCES.keys())
    if args.discipline:
        disciplines = [args.discipline]
    elif not args.all:
        print("Specify --discipline or --all")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_papers = []

    for discipline in disciplines:
        print(f"\n{'='*50}")
        print(f"DISCIPLINE: {discipline.upper()}")
        print(f"{'='*50}")

        papers = search_education_papers(discipline, limit=args.limit, days=args.days)
        print(f"Found {len(papers)} education papers")

        for paper in papers[:5]:
            edu_type = paper.get("education_type", "")
            title = paper.get("title", "")[:60]
            print(f"  [{edu_type}] {title}...")

        # extract visualization concepts
        for paper in papers:
            concept = extract_visualization_concept(paper)
            all_papers.append(concept)

    # save output
    output_file = args.output or str(OUTPUT_DIR / f"education_papers_{datetime.now().strftime('%Y%m%d')}.json")
    with open(output_file, 'w') as f:
        json.dump(all_papers, f, indent=2)

    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Total papers: {len(all_papers)}")
    print(f"Saved to: {output_file}")

    # breakdown by type
    type_counts = {}
    for p in all_papers:
        t = p.get("education_type", "general")
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\nBy type:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()
