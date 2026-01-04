#!/usr/bin/env python3
"""
Generate napkin-style visuals for The Beakers articles
Uses Ollama to create structured visual descriptions
"""

import json
import subprocess
import re
from pathlib import Path

BEAKERS_DIR = Path(__file__).parent.parent
ARTICLES_DIR = BEAKERS_DIR / "articles"

# Prompt to generate SVG-ready visual structure
VISUAL_PROMPT = """You are creating a visual diagram description for an educational infographic.

Given this research summary, create a structured visual description:

RESEARCH: {summary}
NAPKIN_VISUAL: {napkin_visual}

Generate a JSON object with this exact structure for a 4-quadrant infographic:

{{
    "title": "Main concept (3-5 words)",
    "quadrants": [
        {{
            "label": "Category name",
            "icon": "emoji",
            "items": ["item1", "item2", "item3"]
        }},
        {{
            "label": "Category name",
            "icon": "emoji",
            "items": ["item1", "item2"]
        }},
        {{
            "label": "Category name",
            "icon": "emoji",
            "items": ["item1", "item2", "item3"]
        }},
        {{
            "label": "Category name",
            "icon": "emoji",
            "items": ["item1", "item2"]
        }}
    ],
    "flow": ["Step 1", "Step 2", "Step 3", "Outcome"],
    "key_visual": "Description of central image"
}}

Output ONLY valid JSON, no other text."""


def generate_visual_json(article):
    """Generate structured visual JSON from article"""
    summary = f"{article.get('headline', '')}. {article.get('hook', '')} {article.get('findings', '')[:200]}"
    napkin_visual = article.get('napkin_visual', '')

    prompt = VISUAL_PROMPT.format(summary=summary, napkin_visual=napkin_visual)

    try:
        result = subprocess.run(
            ["ollama", "run", "qwen3:latest"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout.strip()

        # Extract JSON from output
        output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL)
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Error: {e}")

    return None


def generate_html_visual(visual_json):
    """Generate HTML/CSS for the visual"""
    if not visual_json:
        return ""

    html = f"""
<div class="napkin-visual">
    <h3 class="napkin-title">{visual_json.get('title', 'Research Overview')}</h3>
    <div class="napkin-grid">
"""

    colors = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']

    for i, quad in enumerate(visual_json.get('quadrants', [])[:4]):
        color = colors[i % len(colors)]
        items_html = ''.join([f'<li>{item}</li>' for item in quad.get('items', [])])
        html += f"""
        <div class="napkin-quadrant" style="border-color: {color}">
            <div class="napkin-icon">{quad.get('icon', '📊')}</div>
            <div class="napkin-label" style="color: {color}">{quad.get('label', '')}</div>
            <ul class="napkin-items">{items_html}</ul>
        </div>
"""

    html += "</div>"

    # Add flow
    flow = visual_json.get('flow', [])
    if flow:
        flow_html = ' → '.join(flow)
        html += f'<div class="napkin-flow">{flow_html}</div>'

    html += "</div>"
    return html


def test_visual():
    """Test with latest article"""
    # Find latest chemistry article
    chem_dir = ARTICLES_DIR / "chemistry"
    articles = sorted(chem_dir.glob("*.json"), reverse=True)

    if not articles:
        print("No articles found")
        return

    with open(articles[0]) as f:
        article = json.load(f)

    print(f"Processing: {article.get('headline', '')[:50]}...")

    visual_json = generate_visual_json(article)
    if visual_json:
        print("\n✅ Generated visual JSON:")
        print(json.dumps(visual_json, indent=2))

        html = generate_html_visual(visual_json)
        print("\n📊 HTML Preview:")
        print(html[:500] + "...")
    else:
        print("❌ Failed to generate visual")


if __name__ == "__main__":
    test_visual()
