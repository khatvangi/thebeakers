#!/usr/bin/env python3
"""
update discipline pages with DEEPDIVES arrays from generated stories
matches story files to database entries by title
"""

import sqlite3
import os
import re
import json
from pathlib import Path

DB_PATH = "data/articles.db"
DEEPDIVE_DIR = "deepdive"

def slugify(title: str) -> str:
    """convert title to filename slug"""
    # strip HTML tags first
    slug = re.sub(r'<[^>]+>', '', title)
    slug = slug.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = slug[:50]  # truncate
    return slug

def get_papers_by_discipline():
    """get all papers grouped by discipline"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT discipline, title, journal, abstract
        FROM society_papers
        ORDER BY discipline, pub_date DESC
    """)

    by_disc = {}
    for disc, title, journal, abstract in cur.fetchall():
        if disc not in by_disc:
            by_disc[disc] = []
        by_disc[disc].append({
            'title': title,
            'journal': journal,
            'abstract': abstract[:200] if abstract else ''
        })

    conn.close()
    return by_disc

def find_story_file(title: str) -> str:
    """find the story HTML file for a paper title"""
    slug = slugify(title)

    # extract key words (first 5 significant words)
    words = [w for w in slug.split('-') if len(w) > 3][:5]

    # look for matching story files
    for f in os.listdir(DEEPDIVE_DIR):
        if f.endswith('-story.html'):
            file_slug = f.replace('-story.html', '')

            # try multiple matching strategies
            # 1. exact start match
            if file_slug.startswith(slug[:30]):
                return f

            # 2. key words match (at least 3 words)
            matches = sum(1 for w in words if w in file_slug)
            if matches >= 3:
                return f

            # 3. partial slug containment
            if slug[:25] in file_slug or file_slug[:25] in slug:
                return f

    return None

def generate_deepdives_js(papers: list, max_items: int = 8) -> str:
    """generate JavaScript DEEPDIVES array"""
    items = []

    for p in papers[:max_items * 2]:  # check more to find matches
        story_file = find_story_file(p['title'])
        if story_file and len(items) < max_items:
            # truncate title for display
            display_title = p['title'][:80] + ('...' if len(p['title']) > 80 else '')
            desc = p['abstract'][:150] + '...' if p['abstract'] else 'Research summary'

            items.append({
                'file': f'deepdive/{story_file}',
                'title': display_title,
                'desc': desc,
                'source': p['journal'] or 'Research Journal'
            })

    if not items:
        return "const DEEPDIVES = [];"

    # format as JS
    js_items = []
    for item in items:
        js_items.append(f"""{{
            file: '{item['file']}',
            title: `{item['title'].replace('`', "'")}`,
            desc: `{item['desc'].replace('`', "'")}`,
            source: '{item['source']}'
        }}""")

    return f"const DEEPDIVES = [\n        " + ",\n        ".join(js_items) + "\n        ];"

def update_discipline_page(discipline: str, deepdives_js: str):
    """update a discipline page with new DEEPDIVES array"""
    page_path = f"{discipline}.html"

    if not os.path.exists(page_path):
        print(f"  [!] {page_path} not found")
        return False

    with open(page_path, 'r') as f:
        content = f.read()

    # replace DEEPDIVES array
    pattern = r'const DEEPDIVES = \[[\s\S]*?\];'

    if re.search(pattern, content):
        new_content = re.sub(pattern, deepdives_js, content, count=1)

        with open(page_path, 'w') as f:
            f.write(new_content)

        return True
    else:
        print(f"  [!] DEEPDIVES not found in {page_path}")
        return False

def main():
    print("=== UPDATING DISCIPLINE PAGES WITH DEEPDIVES ===\n")

    papers = get_papers_by_discipline()

    # map discipline names to page files
    disc_map = {
        'chemistry': 'chemistry',
        'physics': 'physics',
        'biology': 'biology',
        'mathematics': 'mathematics',
        'engineering': 'engineering',
        'ai': 'ai',
        'agriculture': 'agriculture'
    }

    for disc, page in disc_map.items():
        if disc in papers:
            deepdives_js = generate_deepdives_js(papers[disc])

            # count stories found
            count = deepdives_js.count("file:")
            print(f"[{disc.upper()}] {count} stories found")

            if update_discipline_page(page, deepdives_js):
                print(f"  ✓ updated {page}.html")
        else:
            print(f"[{disc.upper()}] no papers in database")

if __name__ == "__main__":
    main()
