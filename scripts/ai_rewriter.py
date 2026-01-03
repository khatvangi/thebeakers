#!/usr/bin/env python3
"""
The Beakers AI Rewriter
Transforms research articles into undergraduate-friendly content
Uses Ollama for local LLM processing
"""

import json
import subprocess
import re
from pathlib import Path
from datetime import datetime

# Configuration
OLLAMA_MODEL = "qwen3:latest"  # Good balance of quality/speed
BEAKERS_DIR = Path(__file__).parent.parent
DATA_DIR = BEAKERS_DIR / "data"
ARTICLES_DIR = BEAKERS_DIR / "articles"

# The KEY prompt - transforms research into student-friendly content
REWRITER_PROMPT = """You are rewriting a research article for The Beakers, a website that makes cutting-edge STEM research accessible to undergraduate students.

Your goal: Make this research EXCITING and CONNECTED to what students are learning in class.

Given this article:
TITLE: {title}
SOURCE: {source}
ABSTRACT/TEASER: {teaser}

Produce the following sections. Be accurate but accessible. Write like a smart friend explaining over coffee.

---

## HEADLINE
Write a catchy, accurate headline (10-15 words). No clickbait, but make students want to read it.

## HOOK
One powerful sentence: Why should an undergrad care about this? The "so what?"

## THE_RESEARCH
(200-250 words)
- What problem were they solving?
- What did they do? (explain methods simply)
- What did they find?
Use analogies. If you use jargon, explain it immediately in parentheses.

## WHY_IT_MATTERS
(100-150 words)
Real-world implications. Future applications. How this could change things.

## CURRICULUM_CONNECTION
(150-200 words) ⭐ THIS IS KEY
- List 2-3 undergraduate courses this relates to (e.g., "CHEM 201 - Organic Chemistry")
- For each course, name 1-2 specific concepts (e.g., "nucleophilic substitution", "reaction mechanisms")
- Explain: "If you understood [X] from your [Course] class, you can understand this research"
- How does reading this ENHANCE their coursework?

## KEY_TERMS
List 5-6 important terms with simple definitions:
- **Term**: Definition (use an analogy if helpful)

## DIFFICULTY
Choose ONE:
- FRESHMAN: General chemistry/physics/bio background is enough
- SOPHOMORE: Needs intro-level major courses
- JUNIOR: Needs upper-division background

## MERMAID_DIAGRAM
Create a simple Mermaid.js flowchart or mind map that visualizes the key concept.
Use this exact format:
```mermaid
graph TD
    A[Starting Point] --> B[Step/Concept]
    B --> C[Result]
```
Keep it simple: 4-6 nodes maximum.

## AUDIO_TEASER
Write exactly 2 sentences (under 50 words) that sound good read aloud. This is for the audio player - make it engaging and conversational.

## THINK_ABOUT
One thought-provoking question that connects this research to a student's everyday life or future career.

---

Output ONLY the sections above. No extra commentary. Start with ## HEADLINE"""


def run_ollama(prompt, model=OLLAMA_MODEL):
    """Run Ollama with the given prompt"""
    try:
        # Use /no_think to skip thinking for faster output
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        print(f"Error running Ollama: {e}")
        return None


def parse_rewritten_article(raw_output):
    """Parse the LLM output into structured sections"""
    sections = {}

    # Strip out <think>...</think> blocks (qwen3 reasoning)
    raw_output = re.sub(r'<think>.*?</think>', '', raw_output, flags=re.DOTALL)

    # Define section patterns
    section_names = [
        'HEADLINE', 'HOOK', 'THE_RESEARCH', 'WHY_IT_MATTERS',
        'CURRICULUM_CONNECTION', 'KEY_TERMS', 'DIFFICULTY',
        'MERMAID_DIAGRAM', 'AUDIO_TEASER', 'THINK_ABOUT'
    ]

    # Split by ## headers
    current_section = None
    current_content = []

    for line in raw_output.split('\n'):
        # Check if this is a section header
        header_match = re.match(r'^##\s*(\w+)', line)
        if header_match:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = header_match.group(1).upper()
            current_content = []
        else:
            if current_section:
                current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    # Extract mermaid diagram code
    if 'MERMAID_DIAGRAM' in sections:
        mermaid_match = re.search(r'```mermaid\s*(.*?)\s*```', sections['MERMAID_DIAGRAM'], re.DOTALL)
        if mermaid_match:
            sections['MERMAID_CODE'] = mermaid_match.group(1).strip()

    return sections


def rewrite_article(article):
    """Rewrite a single article"""
    prompt = REWRITER_PROMPT.format(
        title=article.get('headline', ''),
        source=article.get('source', ''),
        teaser=article.get('teaser', '')
    )

    print(f"  🤖 Sending to {OLLAMA_MODEL}...")
    raw_output = run_ollama(prompt)

    if not raw_output:
        print("  ❌ No response from Ollama")
        return None

    print(f"  ✓ Got response ({len(raw_output)} chars)")

    # Parse into sections
    sections = parse_rewritten_article(raw_output)

    # Build final article object
    rewritten = {
        "original": article,
        "rewritten_at": datetime.now().isoformat(),
        "model": OLLAMA_MODEL,
        "headline": sections.get('HEADLINE', article.get('headline', '')),
        "hook": sections.get('HOOK', ''),
        "research": sections.get('THE_RESEARCH', ''),
        "why_it_matters": sections.get('WHY_IT_MATTERS', ''),
        "curriculum_connection": sections.get('CURRICULUM_CONNECTION', ''),
        "key_terms": sections.get('KEY_TERMS', ''),
        "difficulty": sections.get('DIFFICULTY', 'SOPHOMORE'),
        "mermaid_diagram": sections.get('MERMAID_CODE', ''),
        "audio_teaser": sections.get('AUDIO_TEASER', ''),
        "think_about": sections.get('THINK_ABOUT', ''),
        "raw_output": raw_output
    }

    return rewritten


def save_rewritten_article(article, discipline):
    """Save rewritten article to JSON file"""
    ARTICLES_DIR.mkdir(exist_ok=True)
    disc_dir = ARTICLES_DIR / discipline
    disc_dir.mkdir(exist_ok=True)

    # Create filename from headline
    headline = article.get('headline', 'untitled')
    slug = re.sub(r'[^a-z0-9]+', '-', headline.lower())[:50].strip('-')
    filename = f"{datetime.now().strftime('%Y%m%d')}-{slug}.json"

    filepath = disc_dir / filename
    with open(filepath, 'w') as f:
        json.dump(article, f, indent=2)

    return filepath


def rewrite_from_pending(discipline=None, limit=1):
    """Rewrite articles from pending_articles.json"""
    pending_file = DATA_DIR / "pending_articles.json"
    if not pending_file.exists():
        print("❌ No pending_articles.json found. Run feed_collector.py first.")
        return

    with open(pending_file) as f:
        pending = json.load(f)

    disciplines = [discipline] if discipline else pending.get('disciplines', {}).keys()

    for disc in disciplines:
        disc_data = pending.get('disciplines', {}).get(disc, {})

        # Get articles marked for rewriting (or just take from research)
        articles = disc_data.get('research', [])[:limit]

        if not articles:
            print(f"📂 {disc}: No articles to rewrite")
            continue

        print(f"\n📂 {disc.upper()}: Rewriting {len(articles)} article(s)")

        for i, article in enumerate(articles):
            print(f"\n  [{i+1}/{len(articles)}] {article.get('headline', '')[:60]}...")

            rewritten = rewrite_article(article)

            if rewritten:
                filepath = save_rewritten_article(rewritten, disc)
                print(f"  💾 Saved to: {filepath}")

                # Print preview
                print(f"\n  📰 {rewritten.get('headline', '')}")
                print(f"  🎯 {rewritten.get('hook', '')}")
                print(f"  📊 Difficulty: {rewritten.get('difficulty', '')}")


def test_single_article():
    """Test with a single article"""
    test_article = {
        "headline": "Disulfide-Directed Multicyclic Peptides for Chimeric Antigen Receptors Targeting Solid Tumors",
        "teaser": "Researchers developed new peptide-based targeting molecules for CAR-T cell therapy against solid tumors, using disulfide bonds to create stable multicyclic structures.",
        "source": "Journal of the American Chemical Society",
        "url": "http://dx.doi.org/10.1021/jacs.5c13642",
        "discipline": "chemistry"
    }

    print("🧪 Testing AI Rewriter")
    print("=" * 60)
    print(f"Article: {test_article['headline']}")
    print(f"Source: {test_article['source']}")
    print("=" * 60)

    rewritten = rewrite_article(test_article)

    if rewritten:
        filepath = save_rewritten_article(rewritten, "chemistry")
        print(f"\n✅ Success! Saved to: {filepath}")

        # Pretty print the result
        print("\n" + "=" * 60)
        print("REWRITTEN ARTICLE")
        print("=" * 60)

        print(f"\n📰 HEADLINE:\n{rewritten.get('headline', '')}")
        print(f"\n🎯 HOOK:\n{rewritten.get('hook', '')}")
        print(f"\n🔬 THE RESEARCH:\n{rewritten.get('research', '')}")
        print(f"\n🌍 WHY IT MATTERS:\n{rewritten.get('why_it_matters', '')}")
        print(f"\n📚 CURRICULUM CONNECTION:\n{rewritten.get('curriculum_connection', '')}")
        print(f"\n📖 KEY TERMS:\n{rewritten.get('key_terms', '')}")
        print(f"\n📊 DIFFICULTY: {rewritten.get('difficulty', '')}")
        print(f"\n📈 MERMAID DIAGRAM:\n```mermaid\n{rewritten.get('mermaid_diagram', '')}\n```")
        print(f"\n🎧 AUDIO TEASER:\n{rewritten.get('audio_teaser', '')}")
        print(f"\n🤔 THINK ABOUT:\n{rewritten.get('think_about', '')}")

        return rewritten
    else:
        print("❌ Rewriting failed")
        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_single_article()
        elif sys.argv[1] == "rewrite":
            discipline = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            rewrite_from_pending(discipline, limit)
    else:
        print("Usage:")
        print("  python ai_rewriter.py test              - Test with sample article")
        print("  python ai_rewriter.py rewrite           - Rewrite 1 article from each discipline")
        print("  python ai_rewriter.py rewrite chemistry 3 - Rewrite 3 chemistry articles")
