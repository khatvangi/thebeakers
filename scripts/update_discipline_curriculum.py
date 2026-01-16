#!/usr/bin/env python3
"""
update_discipline_curriculum.py - update discipline pages with curriculum.json data

replaces hardcoded CURRICULUM JavaScript objects in discipline pages
with real data from curriculum.json.

usage:
    python update_discipline_curriculum.py              # update all disciplines
    python update_discipline_curriculum.py chemistry    # update one discipline
    python update_discipline_curriculum.py --dry-run    # show changes without writing
"""

import argparse
import json
import re
from pathlib import Path

# paths
SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
CURRICULUM_PATH = PROJECT_DIR / "data" / "curriculum.json"


def load_curriculum() -> dict:
    """load curriculum.json"""
    with open(CURRICULUM_PATH) as f:
        return json.load(f)


def generate_curriculum_js(discipline: str, curriculum: dict) -> str:
    """generate JavaScript CURRICULUM object for a discipline"""

    if discipline not in curriculum:
        return "const CURRICULUM = {};"

    disc_data = curriculum[discipline]
    lines = ["        const CURRICULUM = {"]

    for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
        topics = subfield_data.get("topics", [])
        difficulty = subfield_data.get("difficulty", "sophomore")
        level = subfield_data.get("level", "200-300")

        lines.append(f"            '{subfield_name}': [")

        for topic in topics:
            topic_name = topic["name"]
            topic_slug = topic["slug"]
            # url points to a future topic page
            url = f"#topic-{topic_slug}"
            lines.append(f"                {{ topic: '{topic_name}', url: '{url}' }},")

        lines.append("            ],")

    lines.append("        };")

    return "\n".join(lines)


def update_discipline_page(discipline: str, curriculum: dict, dry_run: bool = False) -> bool:
    """update a discipline page with curriculum data"""

    page_path = PROJECT_DIR / f"{discipline}.html"

    if not page_path.exists():
        print(f"[!] page not found: {page_path}")
        return False

    content = page_path.read_text()

    # find and replace CURRICULUM object
    # pattern matches: const CURRICULUM = { ... };
    pattern = r"(const CURRICULUM = \{[\s\S]*?\n        \};)"

    new_curriculum_js = generate_curriculum_js(discipline, curriculum)

    if not re.search(pattern, content):
        print(f"[!] could not find CURRICULUM object in {page_path.name}")
        return False

    new_content = re.sub(pattern, new_curriculum_js, content)

    if new_content == content:
        print(f"  {discipline}: no changes needed")
        return True

    if dry_run:
        print(f"  {discipline}: would update CURRICULUM object")
        # show a preview
        lines = new_curriculum_js.split('\n')
        for line in lines[:10]:
            print(f"    {line}")
        if len(lines) > 10:
            print(f"    ... ({len(lines) - 10} more lines)")
        return True

    page_path.write_text(new_content)
    print(f"  {discipline}: updated")
    return True


def main():
    parser = argparse.ArgumentParser(description="Update discipline pages with curriculum data")
    parser.add_argument("discipline", nargs="?", help="Discipline to update (or all)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    curriculum = load_curriculum()

    # get list of disciplines
    disciplines = [k for k in curriculum.keys() if not k.startswith("_")]

    if args.discipline:
        if args.discipline not in disciplines:
            print(f"[!] unknown discipline: {args.discipline}")
            print(f"    available: {', '.join(disciplines)}")
            return
        disciplines = [args.discipline]

    print("\n=== UPDATING DISCIPLINE PAGES ===\n")

    for discipline in disciplines:
        update_discipline_page(discipline, curriculum, args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
