# GUIDELINES

## APPROACH

keep things SIMPLE
strive fro simplicity, clarity an brevity in code

* Don't jump into writing code, DISCUSS the approach FIRST
  - then critique your own approach
  - then come up with the best one based on the two: first + critique
* Do not be overly optimistic: when you are are missing and brushing off the truth. TRUTH, REAL, nou rushed ROOT CAUSE matter a lot more than optimistic answers.
* (!) DON NOT rush into writing code
* if and when writing code, try to stay minimalistic: more code is harder to maintain
* in case the knowledge can be incomplete given the temporality of the question browse for the latest intel
  - do not use the browsed intel as is though, is your own intelligence with the latest intel as an additional referece
* write code ONLY when asked. small, few lines of code are fine, but do not write a whole file or a big chunk of code until prompted to do so

## (!) DO NOT CONSTANTLY AGREEE

 * think analytically and critically. the goal is to reach to a solution that works vs. make me feel good

## WHEN SHOW CODE CHANGES

1. show the previous couple of lines after which the changes are needed
2. and make the changes with comments similar to "## CHANGE NEEDED HERE"
3. and a couple of lines after with a "## CHANGE ENDS HERE" before them

## VALIDATION

Ideas, tests or code, don't rush into conclusions, be super critical and analytical with outmost attention to detail

## PROBLEM SOLVING

* if the data and/or code is avaliable, don't guess (i.e. potenially, likely, could be) the root cause, analyze the code and find it
* look for the root cause, search through the code, get to the bottom vs. assuming the root cause
* divide and conquer: break down the problem into smaller parts, solve each part, then combine them

## CODING

* keep solutions and code as SIMPLE as possible without sacrificing functionality
* never capitalize comments
* strive for good function names: e.g. not "get"s. prefer "findMeaning" vs. "getMeaning"
* when a simple update is needed, don't rewrite the whole file, explain what needs to be updated, where and why
* when providing a fix or a change, don't update the documentation | file header, etc.. just add a comment where the change is made

# The Beakers

STEM research rewritten for undergraduate students. Cutting-edge research translated into language students can understand, connected to what they're learning in class.

**Live site:** https://thebeakers.com
**Launch:** Monday, January 6, 2026

## Vision

- Research papers rewritten for undergraduates with curriculum connections
- Show students how their coursework applies to real research
- Difficulty levels: Freshman, Sophomore, Junior+
- No AI slop, no clickbait, academic honesty

**Motto:** व्यये कृते वर्धत एव नित्यं — "Knowledge always grows when shared" (Chanakya Niti)

## DO NOT REINVENT - USE EXISTING CODE

**CRITICAL: Always use existing scripts and templates. Never create new ones from scratch.**

### Canonical Templates (LOCKED - DO NOT MODIFY)
| Purpose | File | Best For |
|---------|------|----------|
| Deep Dive | `deepdive/solar-cell-bromine.html` | Full NotebookLM treatment |
| **Explain Visual** | `deepdive/solar-cell-bromine-visual.html` | Quick overview, data-heavy, comparisons |
| **Explain Story** | `deepdive/solar-cell-bromine-story.html` | Complex concepts, step-by-step |

### Canonical Prompts (LOCKED - DO NOT MODIFY)
| Format | Prompt File |
|--------|-------------|
| Visual Summary | `/storage/napkin/prompts/explain-visual.txt` |
| Detailed Story | `/storage/napkin/prompts/explain-story.txt` |
| TL;DR | `/storage/napkin/prompts/tldr.txt` |

### Canonical Scripts (USE THESE)
| Purpose | Script | Command |
|---------|--------|---------|
| Weekly pipeline | `scripts/weekly_pipeline.py` | `python scripts/weekly_pipeline.py` |
| Explain generator | `/storage/napkin/src/explain_generator.py` | Import and use functions |
| Feed collection | `scripts/feed_collector.py` | `python scripts/feed_collector.py` |

### Rules
1. **NEVER** create new HTML templates - copy solar-cell-bromine-*.html
2. **NEVER** modify the locked templates or prompts
3. **ALWAYS** use one of the two explain formats (Visual or Story)
4. **ALWAYS** copy CSS/styling exactly from the canonical templates
5. **ALWAYS** check existing code before writing new code
6. When in doubt, ask: "Is there existing code for this?"

### Explain Format: Visual Summary
Quick visual overview with cards, grids, progress bars. NO Mermaid.

**Structure (from solar-cell-bromine-visual.html):**
1. Hero with 3 key stats
2. The Challenge (3 visual cards)
3. The Research Question (flow diagram)
4. The Comparison (molecule-comparison cards)
5. Why It Works (mechanism-grid, 4 cards)
6. Results Timeline (progress bars)
7. Key Insight Box

**Visual Elements:** Lucide icons, visual-card grid, comparison cards, mechanism-grid, timeline-bars, insight-box

### Explain Format: Detailed Story
8-scene narrative with Mermaid diagrams.

**Structure (from solar-cell-bromine-story.html):**
1. The Challenge (mindmap)
2. The Hypothesis (flowchart)
3. The Experiment (flowchart)
4. The Method (flowchart)
5. The Surprise/Results (flowchart + stats-grid + highlight-box)
6. The Explanation (mindmap)
7. The Achievement (timeline + highlight-box)
8. The Implication (flowchart + takeaway highlight-box)

**Visual Elements:** Mermaid diagrams (mindmap, flowchart, timeline), highlight-box, stats-grid

### TL;DR Format (LOCKED)
One sentence (max 2) summary for quick scanning.

**Structure:**
```
[Researchers/Team] [action verb] [what they did/found], which [why it matters].
```

**Rules:**
- ONE sentence (two max)
- Active voice ("Researchers discovered" not "It was discovered")
- Simple words (no jargon)
- Concrete benefit (why should a student care?)
- No citations, no journal names
- Plain text only (no HTML)

**Example:**
"Researchers discovered that adding bromine to the center of solar cell molecules boosts efficiency to 20% — flipping decades of conventional wisdom."

## Content Strategy

### Three Formats (Source-Based Guidelines)

Choose format based on source type (flexible, use judgment):

| Source Type | Format | Description |
|-------------|--------|-------------|
| **Review journals** | Deep Dive | Full NotebookLM treatment: podcast, video, quiz |
| **Education journals** | Visual Summary | Icons, SVGs, progress bars - quick visual grasp |
| **High-impact journals** | Detailed Story | Text narrative + Mermaid diagrams |

**Not rigid** - pick format that best fits each paper.

### Format Details

1. **Deep Dive** (`deepdive/[slug].html`)
   - Processed through Google NotebookLM
   - Assets: Podcast, Video, Mind Map, Infographic, Study Guide
   - Our value-add: Curriculum Connection + Interactive Quiz
   - Media: SoundCloud (podcast) + YouTube (video)

2. **Visual Summary** (`deepdive/[slug]-visual.html`)
   - Lucide icons, SVG diagrams, progress bars
   - Quick visual overview, minimal text
   - Generated with napkin-local

3. **Detailed Story** (`deepdive/[slug]-story.html`)
   - Text narrative (2-3 paragraphs per section)
   - Mermaid diagrams reinforcing concepts (hover to enlarge, click to fullscreen)
   - Curriculum Connection section with course links
   - For papers needing more explanation

### Source Selection
- **Review journals**: Comprehensive peer-reviewed articles
- **Education journals**: Written for students
- **High-impact journals**: Top research journals

## Qdrant + Curriculum Integration (SIGNATURE FEATURE)

**Our key differentiator** - Every article connects to undergraduate curriculum.

### Architecture
```
Qdrant (localhost:6333)
├── chunks_text (9,884 points) - LibreTexts textbooks (665 books)
├── quizzes_questions - Quiz bank (to populate)
└── chunks_hybrid - Hybrid search
```

### Difficulty Levels
| Level | Course | LibreTexts Category |
|-------|--------|---------------------|
| Freshman | 100-200 | Introductory, General |
| Sophomore | 200-300 | Organic, Intermediate |
| Junior | 300-400 | Physical, Analytical, Advanced |

### Workflow
1. **Paper comes in** → Query Qdrant for matching curriculum
2. **Identify level** → Based on which LibreTexts category matches
3. **Generate connection** → List related topics + prerequisites
4. **Generate quizzes** → Questions at appropriate difficulty

### Key Commands
```bash
# Query RAG for curriculum
source /storage/RAG/.venv/bin/activate
python /storage/RAG/src/query.py "YOUR TOPIC"

# Interactive chat
python /storage/RAG/src/chat.py
```

### Full Documentation
See `docs/CURRICULUM_QDRANT_INTEGRATION.md` for complete details.

## Content Modes (Simplified)

| Mode | Name | Source | Processing |
|------|------|--------|------------|
| Tacos | Visual Summaries | Single PDF | Local templates |
| Big Enchilada | Deep Dives | Collection of PDFs | NotebookLM full treatment |

Both include: Curriculum Connection + Quizzes (from Qdrant)

## Site Structure

```
thebeakers.com/
├── index.html              # Main page with cards, animations, newsletter
├── [discipline].html       # 7 discipline pages (chemistry, physics, etc.)
├── article.html            # Regular article page (dynamic, loads from JSON)
├── deepdive/
│   └── [slug].html         # Deep Dive articles (static, rich media)
├── articles/
│   └── [discipline]/
│       ├── index.json      # Auto-generated article index
│       └── *.json          # Rewritten articles
├── data/
│   ├── articles.db         # SQLite: seen_articles, archive tables
│   └── pending_articles.json
└── scripts/
    ├── society_fetcher.py  # Fetch from society journals (ACS, APS, etc.)
    ├── feed_collector.py   # v2: Curated RSS collector
    ├── ai_rewriter.py      # Ollama rewriter for regular articles
    └── generate_indexes.py # Generate article index files
```

## Disciplines

| Category | Disciplines |
|----------|-------------|
| Natural Sciences | Biology, Chemistry, Physics, Agriculture |
| Technology | Artificial Intelligence |
| Engineering | Engineering (Civil, Mechanical, Electrical, Chemical) |
| Mathematics | Mathematics |

## Weekly Workflow

### 1. Collect Articles (Monday)
```bash
python scripts/feed_collector.py           # Collect from all feeds
python scripts/feed_collector.py deepdive  # Show Deep Dive candidates
```

### 2. Pick & Process Deep Dives (Monday-Tuesday)

**For each of 7 disciplines:**

1. **Select article** from review/education sources
2. **Find PDF** (Open Access, institutional, or Sci-Hub)
3. **NotebookLM** (notebooklm.google.com):
   - Create notebook → Upload PDF
   - Generate: Podcast, Video, Study Guide, Briefing Doc
   - Download all assets
4. **Upload media:**
   - Podcast (audio) → SoundCloud
   - Video → YouTube
5. **Give Claude:**
   - Article title + discipline
   - SoundCloud URL
   - YouTube URL
   - Infographic/mind map images
   - Key points for quiz questions

Claude builds `deepdive/[slug].html` with embeds + Curriculum Connection + Quiz.

### 3. Rewrite Regular Articles (Tuesday-Wednesday)
```bash
python scripts/ai_rewriter.py rewrite chemistry 3
python scripts/ai_rewriter.py rewrite physics 3
# ... for each discipline
python scripts/generate_indexes.py
```

### 4. Publish (Wednesday)
```bash
git add . && git commit -m "Week X articles" && git push
```

## Feed Collector v2

Curated sources organized by type:

```python
FEEDS = {
    "chemistry": {
        "review": [        # Deep Dive candidates
            ("Chemical Reviews", "..."),      # IF 62
            ("Chem Society Reviews", "..."),  # IF 46
        ],
        "high_impact": [   # Regular summaries
            ("JACS", "..."),                  # IF 15
            ("Nature Chemistry", "..."),      # IF 24
        ],
        "education": [     # Deep Dive candidates
            ("J. Chem. Education", "..."),
        ]
    },
    # ... similar for other disciplines
}
```

Database tracks seen articles to avoid duplicates:
- `seen_articles`: All collected articles with status
- `archive`: Approved/published articles

## Deep Dive Page Template

Located at `deepdive/solar-cell-bromine.html` as reference.

Sections:
1. Hero with title and metadata
2. Podcast player (YouTube embed)
3. Video player (YouTube embed)
4. Infographic display
5. **Curriculum Connection** (our value-add)
6. **Interactive Quiz** (our value-add) - JavaScript-based
7. Mind Map
8. Glossary
9. Downloads (PDF study guide, etc.)

## Design

### Theme
- Dark background (#0f172a)
- Card-based layout with Midjourney illustrations
- Plus Jakarta Sans + Instrument Serif fonts

### Color Palette
```css
--bg-dark: #0f172a
--bg-card: #1e293b
--accent-green: #10b981  (Natural Sciences)
--accent-blue: #3b82f6   (Technology)
--accent-orange: #f59e0b (Engineering)
--accent-purple: #8b5cf6 (Mathematics)
--accent-cyan: #06b6d4   (Deep Dive accent)
```

## Deployment

- **Hosting:** Cloudflare Pages (auto-deploy from GitHub)
- **Repo:** https://github.com/khatvangi/thebeakers
- **Domain:** thebeakers.com (Cloudflare DNS)
- **Media Hosting:** (Cloudflare Pages has 25MB file limit)
  - Podcasts → SoundCloud (free, audio-only)
  - Videos → YouTube (free)

## Related Sites

- **SPS Daily:** https://spsdaily.thebeakers.com
- **Newsletter:** https://newsletter.thebeakers.com (Listmonk)

## Current Status (Jan 2026)

- [x] All 7 discipline pages created
- [x] Feed collector v2 with curated sources
- [x] 21 articles published (3 per discipline)
- [x] Deep Dive template created (solar-cell-bromine)
- [x] Solar cell Deep Dive complete (Chemistry)
  - Video: https://www.youtube.com/watch?v=fZc-jc7PZEc
  - Podcast: https://soundcloud.com/thebeakerscom/bromine_core_reaches_20
- [x] Legged Locomotion Deep Dive complete (Engineering)
  - Detailed Story: `deepdive/legged-locomotion-story.html`
  - Visual Summary: `deepdive/legged-locomotion-visual.html`
  - Source: Ha et al., IJRR 2025 (32-page survey)
  - Curriculum Connection: 6 courses (ME, EECS, CS, MATH)
- [ ] Public launch announcement (Monday, Jan 6)

## Contact

- **Founding Editor:** Kiran Boggavarapu
- **Email:** thebeakerscom@gmail.com
