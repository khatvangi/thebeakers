#!/usr/bin/env python3
"""
Generate article indexes for The Beakers
Creates JSON indexes for each discipline listing all available articles
"""

import json
from pathlib import Path
from datetime import datetime

BEAKERS_DIR = Path(__file__).parent.parent
ARTICLES_DIR = BEAKERS_DIR / "articles"
DATA_DIR = BEAKERS_DIR / "data"

DISCIPLINES = ["chemistry", "physics", "biology", "mathematics", "engineering", "agriculture", "ai"]


def generate_discipline_index(discipline):
    """Generate index.json for a discipline"""
    disc_dir = ARTICLES_DIR / discipline

    if not disc_dir.exists():
        return None

    articles = []

    for json_file in sorted(disc_dir.glob("*.json"), reverse=True):
        try:
            with open(json_file) as f:
                article = json.load(f)

            articles.append({
                "filename": json_file.name,
                "headline": article.get("headline", ""),
                "hook": article.get("hook", ""),
                "difficulty": article.get("difficulty", "SOPHOMORE"),
                "source": article.get("original", {}).get("source", ""),
                "rewritten_at": article.get("rewritten_at", "")
            })
        except Exception as e:
            print(f"  Error reading {json_file}: {e}")

    if articles:
        index_path = disc_dir / "index.json"
        with open(index_path, 'w') as f:
            json.dump({
                "discipline": discipline,
                "count": len(articles),
                "updated": datetime.now().isoformat(),
                "articles": articles
            }, f, indent=2)
        return index_path

    return None


def generate_all_indexes():
    """Generate indexes for all disciplines"""
    print("Generating article indexes...")

    for discipline in DISCIPLINES:
        result = generate_discipline_index(discipline)
        if result:
            print(f"  {discipline}: {result}")
        else:
            print(f"  {discipline}: No articles")

    print("Done!")


if __name__ == "__main__":
    generate_all_indexes()
