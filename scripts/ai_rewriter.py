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
# This is comprehensive - we want SUBSTANTIAL content, not token summaries
REWRITER_PROMPT = """You are rewriting a research article for The Beakers, a website that makes cutting-edge STEM research accessible to undergraduate students.

Your goal: Make this research EXCITING and deeply CONNECTED to what students are learning in class. This is not a summary - it's a bridge between classroom learning and real research.

Given this article:
TITLE: {title}
SOURCE: {source}
ABSTRACT/TEASER: {teaser}

Produce the following sections. Be accurate but accessible. Write like a brilliant teaching assistant who genuinely wants students to understand.

---

## HEADLINE
Write a catchy, accurate headline (10-15 words). No clickbait, but make students want to read it.

## HOOK
One powerful sentence: Why should an undergrad care about this? Connect it to their future career or something they experience daily.

## THE_RESEARCHERS
(50-75 words)
Who did this research? What institution? If you don't know specifics, describe the type of research group (e.g., "A team of biochemists and oncologists at a major research university..."). Why are they qualified to tackle this problem? This humanizes the science.

## THE_PROBLEM
(100-150 words)
What problem were they trying to solve? Why does this problem matter?
- What's the current limitation or gap in knowledge?
- Why have previous approaches failed or fallen short?
- What would solving this problem mean for the field?
Paint a picture of why this research was needed.

## THE_APPROACH
(150-200 words)
How did they tackle this problem? Explain the methodology in plain language.
- What was their key insight or novel approach?
- What techniques did they use? (explain each briefly)
- What made their approach different from previous attempts?
Use analogies liberally. If you mention a technique, immediately explain what it does in parentheses.

## KEY_FINDINGS
(150-200 words)
What did they discover? Be specific about results.
- What were the main findings?
- How significant are these results? (quantify if possible)
- Were there any surprising discoveries?
- What are the limitations they acknowledged?

## WHY_IT_MATTERS
(100-150 words)
Real-world implications. Future applications. How this could change things for patients, technology, society.

## CURRICULUM_CONNECTION
⭐⭐⭐ THIS IS THE MOST IMPORTANT SECTION - BE THOROUGH ⭐⭐⭐
(400-500 words minimum)

This section bridges classroom learning to real research. For each course, explain IN DEPTH how concepts students learned apply here.

**Format for each course:**

### [COURSE CODE] - [Course Name]
**Key concepts from this course that appear in this research:**
- **[Concept 1]**: Explain how this concept from class directly applies to the research. Be specific. If there's an equation, mention it. If there's a lab technique they've done, connect it.
- **[Concept 2]**: Same treatment.

**"Remember when you learned..."**: Write 2-3 sentences that start with something like "Remember when you learned about [X] in [Course]? This research is [X] in action. The researchers used exactly this principle when they..."

Cover AT LEAST 3 courses. For each course, include:
1. The specific chapter/topic from a typical syllabus
2. At least 2 specific concepts with detailed explanations
3. A "remember when" connection
4. If applicable: relevant equations, lab techniques, or problem types they've solved

Example courses to consider (pick what's relevant):
- General Chemistry: bonding, thermodynamics, kinetics, equilibrium
- Organic Chemistry: functional groups, reaction mechanisms, stereochemistry, synthesis
- Biochemistry: protein structure, enzyme kinetics, metabolic pathways
- Physical Chemistry: quantum mechanics, spectroscopy, thermodynamics
- Analytical Chemistry: spectroscopy, chromatography, electrochemistry
- Biology: cell biology, genetics, molecular biology, physiology
- Physics: mechanics, E&M, quantum, statistical mechanics
- Mathematics: calculus, differential equations, linear algebra, statistics

End with a paragraph: "Reading this research enhances your coursework by showing you that [concepts] aren't just textbook exercises—they're the foundation of how scientists solve real problems."

## KEY_TERMS
List 6-8 important terms with clear definitions:
- **Term**: Definition. Use an analogy if helpful. (2-3 sentences each)

## DIFFICULTY
Choose ONE and explain briefly why:
- FRESHMAN: General chemistry/physics/bio background is enough
- SOPHOMORE: Needs intro-level major courses (organic, biochem, etc.)
- JUNIOR: Needs upper-division background (physical chem, advanced bio, etc.)

## CONCEPT_MAP
Create a Mermaid.js diagram that shows the CONCEPTUAL RELATIONSHIPS in this research (not a flowchart of steps).
Show how ideas connect: problem → approach → key insight → findings → implications.
Use this format:
```mermaid
mindmap
  root((Central Concept))
    Problem
      Current limitation
      Why it matters
    Approach
      Key technique 1
      Key technique 2
    Discovery
      Finding 1
      Finding 2
    Impact
      Application 1
      Future direction
```
Make it educational - someone should understand the research structure from this diagram alone.

## AUDIO_TEASER
Write exactly 3 sentences (under 75 words) that sound good read aloud. This is for the audio player - make it engaging, conversational, and make listeners want to read more.

## THINK_ABOUT
One thought-provoking question that connects this research to a student's everyday life, future career, or a bigger scientific question they might explore.

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

    # Split by ## headers (handles multi-word headers like "## THE_RESEARCHERS")
    current_section = None
    current_content = []

    for line in raw_output.split('\n'):
        # Check if this is a section header (## followed by word characters and underscores)
        header_match = re.match(r'^##\s*([A-Z_]+)', line)
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

    # Extract mermaid diagram code from CONCEPT_MAP (or legacy MERMAID_DIAGRAM)
    for key in ['CONCEPT_MAP', 'MERMAID_DIAGRAM']:
        if key in sections:
            mermaid_match = re.search(r'```mermaid\s*(.*?)\s*```', sections[key], re.DOTALL)
            if mermaid_match:
                sections['MERMAID_CODE'] = mermaid_match.group(1).strip()
                break

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

    # Build final article object with expanded sections
    rewritten = {
        "original": article,
        "rewritten_at": datetime.now().isoformat(),
        "model": OLLAMA_MODEL,
        # Core content
        "headline": sections.get('HEADLINE', article.get('headline', '')),
        "hook": sections.get('HOOK', ''),
        # The Research (expanded into parts)
        "researchers": sections.get('THE_RESEARCHERS', ''),
        "problem": sections.get('THE_PROBLEM', ''),
        "approach": sections.get('THE_APPROACH', ''),
        "findings": sections.get('KEY_FINDINGS', ''),
        # Legacy field for backwards compatibility
        "research": sections.get('THE_RESEARCH', ''),
        # Impact
        "why_it_matters": sections.get('WHY_IT_MATTERS', ''),
        # THE BIG ENCHILADA
        "curriculum_connection": sections.get('CURRICULUM_CONNECTION', ''),
        # Supporting content
        "key_terms": sections.get('KEY_TERMS', ''),
        "difficulty": sections.get('DIFFICULTY', 'SOPHOMORE'),
        "concept_map": sections.get('MERMAID_CODE', ''),
        # Legacy field name
        "mermaid_diagram": sections.get('MERMAID_CODE', ''),
        # Audio and reflection
        "audio_teaser": sections.get('AUDIO_TEASER', ''),
        "think_about": sections.get('THINK_ABOUT', ''),
        # Raw output for debugging
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
        print(f"\n👩‍🔬 THE RESEARCHERS:\n{rewritten.get('researchers', '')}")
        print(f"\n❓ THE PROBLEM:\n{rewritten.get('problem', '')}")
        print(f"\n🔧 THE APPROACH:\n{rewritten.get('approach', '')}")
        print(f"\n💡 KEY FINDINGS:\n{rewritten.get('findings', '')}")
        print(f"\n🌍 WHY IT MATTERS:\n{rewritten.get('why_it_matters', '')}")
        print(f"\n" + "=" * 60)
        print("⭐ CURRICULUM CONNECTION (THE BIG ENCHILADA):")
        print("=" * 60)
        print(f"{rewritten.get('curriculum_connection', '')}")
        print("=" * 60)
        print(f"\n📖 KEY TERMS:\n{rewritten.get('key_terms', '')}")
        print(f"\n📊 DIFFICULTY: {rewritten.get('difficulty', '')}")
        print(f"\n🗺️ CONCEPT MAP:\n```mermaid\n{rewritten.get('concept_map', '')}\n```")
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
