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

### Canonical Templates (COPY THESE EXACTLY)
| Purpose | File | Notes |
|---------|------|-------|
| Deep Dive | `deepdive/solar-cell-bromine.html` | Full NotebookLM treatment |
| Explain Article | `deepdive/legged-locomotion-story.html` | Chapters + Mermaid diagrams |
| Explain Prompt | `/storage/napkin/prompts/explain-story.txt` | **USE THIS PROMPT** |

### Canonical Scripts (USE THESE)
| Purpose | Script | Command |
|---------|--------|---------|
| Weekly pipeline | `scripts/weekly_pipeline.py` | `python scripts/weekly_pipeline.py` |
| Visual stories | `/storage/napkin/src/visual_story.py` | `generate_story_scenes()`, `generate_visual_story_html()` |
| Feed collection | `scripts/feed_collector.py` | `python scripts/feed_collector.py` |

### Rules
1. **NEVER** create new HTML templates - copy existing ones
2. **NEVER** change the chapter structure without explicit permission
3. **ALWAYS** use `/storage/napkin/prompts/explain-story.txt` prompt for explain articles
4. **ALWAYS** copy styling from `deepdive/legged-locomotion-story.html`
5. **ALWAYS** check existing code before writing new code
6. When in doubt, ask: "Is there existing code for this?"

### Explain Article Structure (Chapter-Based)
Each explain article has 5-7 chapters with Mermaid diagrams. See `/storage/napkin/prompts/explain-story.txt`.

**Chapter Flow:**
1. **The Problem/Promise** - Why this matters
2. **Background/Evolution** - Historical context
3. **The Method** - How it works (+ Mermaid diagram)
4. **Key Innovation** - What's new (+ highlight-box)
5. **Results** - What they found (+ key-insight)
6. **Implications** - Why it matters
7. **Road Ahead** - Future directions

**Visual Elements:**
- Mermaid diagrams (2-3 per article)
- Key insight boxes (pink accent)
- Highlight boxes (green/cyan gradient)
- Comparison grids (for comparing methods)
- Timeline (for historical evolution)

**Reference:** `deepdive/legged-locomotion-story.html`

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
- **NO arXiv**: Not peer-reviewed

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
