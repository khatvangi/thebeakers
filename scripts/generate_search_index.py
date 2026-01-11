#!/usr/bin/env python3
"""
generate_search_index.py - build master index for search and browse

outputs:
- /storage/thebeakers/data/articles-index.json (all articles, sorted by date)
"""

import json
from pathlib import Path
from datetime import datetime

ARTICLES_DIR = Path("/storage/thebeakers/articles")
OUTPUT_FILE = Path("/storage/thebeakers/data/articles-index.json")

DISCIPLINES = ["biology", "chemistry", "physics", "ai", "engineering", "mathematics", "agriculture"]


def load_discipline_articles(discipline: str) -> list:
    """load articles from discipline index.json"""
    index_file = ARTICLES_DIR / discipline / "index.json"
    if not index_file.exists():
        return []

    data = json.loads(index_file.read_text())
    articles = []

    for article in data.get("articles", []):
        filename = article.get("filename", "")
        if filename == "index.json" or not filename:
            continue

        # extract date from filename (YYYYMMDD-slug.json)
        date_str = filename[:8] if len(filename) > 8 else ""
        try:
            date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            date = ""

        articles.append({
            "discipline": discipline,
            "filename": filename,
            "headline": article.get("headline", ""),
            "hook": article.get("hook", ""),
            "difficulty": article.get("difficulty", ""),
            "source": article.get("source", ""),
            "date": date,
            "url": f"/articles/{discipline}/{filename.replace('.json', '')}"
        })

    return articles


def main():
    all_articles = []

    for discipline in DISCIPLINES:
        articles = load_discipline_articles(discipline)
        all_articles.extend(articles)
        print(f"  {discipline}: {len(articles)} articles")

    # sort by date (newest first)
    all_articles.sort(key=lambda x: x.get("date", ""), reverse=True)

    # build index
    index = {
        "generated": datetime.now().isoformat(),
        "count": len(all_articles),
        "articles": all_articles
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    print(f"\nwrote {len(all_articles)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
