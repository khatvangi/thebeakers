# The Beakers

STEM research rewritten for undergraduate students. Cutting-edge research translated into language students can understand, connected to what they're learning in class.

**Live site:** https://thebeakers.com

## Vision

- Research papers rewritten for undergraduates with curriculum connections
- Show students how their coursework applies to real research
- Difficulty levels: Freshman, Sophomore, Junior+
- No AI slop, no clickbait, academic honesty

**Motto:** व्यये कृते वर्धत एव नित्यं — "Knowledge always grows when shared" (Chanakya Niti)

## Site Structure

```
thebeakers.com/
├── index.html              # Main page with cards, animations, newsletter
├── index-v1.html           # Backup: Original dark theme with tags
├── index-v2.html           # Backup: Light cream theme with cards
├── chemistry.html          # Chemistry discipline page (template for others)
├── article.html            # Individual article page (dynamic, loads from JSON)
├── logo.png                # Main logo (transparent)
├── logo-48.png             # Header logo
├── favicon.ico             # Browser favicon
├── [discipline].png        # Card images (biology, chemistry, physics, etc.)
├── articles/
│   └── [discipline]/
│       ├── index.json      # Auto-generated article index
│       └── *.json          # Rewritten articles (one per article)
├── data/
│   ├── pending_articles.json   # Collected articles awaiting curation
│   └── approved_articles.json  # Curator-approved articles
└── scripts/
    ├── feed_collector.py       # RSS feed collector (7 disciplines)
    ├── ai_rewriter.py          # Article rewriter using Ollama/qwen3
    ├── telegram_curator.py     # Telegram bot for curation
    └── generate_indexes.py     # Generate article index files
```

## Disciplines (Card Categories)

### Natural Sciences
- Biology - biology.png
- Chemistry - chemistry.png
- Physics - physics.png
- Agriculture - agriculture.png

### Technology
- Artificial Intelligence - ai.png

### Engineering
- Engineering (Civil, Mechanical, Electrical, Chemical) - engineering.png

### Mathematics
- Mathematics - mathematics.png

## Design

### Theme
- Dark background (#0f172a)
- Card-based layout with Midjourney illustrations
- Plus Jakarta Sans + Instrument Serif fonts
- Inspired by writingexamples.com (Webby award winner)

### Animations
- Hero text slide-up on load
- Motto fade-in with delay
- Cards fade-in on scroll (staggered via Intersection Observer)
- Card image zoom on hover
- Swoosh animation around newsletter form
- Smooth scroll navigation

### Color Palette
```css
--bg-dark: #0f172a
--bg-card: #1e293b
--accent-green: #10b981  (Natural Sciences)
--accent-blue: #3b82f6   (Technology)
--accent-orange: #f59e0b (Engineering)
--accent-purple: #8b5cf6 (Mathematics)
```

## Sections

1. **Hero** - Title, tagline, Chanakya quote
2. **Disciplines** - 7 cards with category images
3. **Beyond Articles** - Podcasts & Curated Videos
   - Weekly Podcasts: This Week in Chemistry/Engineering/Biology/Math
   - Curated Videos: Lecture highlights, lab demos, concept explainers
4. **Newsletter** - Email signup with swoosh animation
5. **Footer** - Founding Editor, links

## Deployment

- **Hosting:** Cloudflare Pages
- **Repo:** https://github.com/khatvangi/thebeakers
- **Domain:** thebeakers.com (Cloudflare DNS)

## Related Sites

- **SPS Daily:** https://spsdaily.thebeakers.com — Science, Philosophy & Society digest
- **Course:** https://course.thebeakers.com — (placeholder)
- **Newsletter:** https://newsletter.thebeakers.com — Listmonk instance

## Article Pipeline

### 1. Collection (Weekly)
```bash
python scripts/feed_collector.py
```
- Collects from research + education journals for 7 disciplines
- Saves to `data/pending_articles.json`

### 2. Curation (Telegram Bot)
```bash
python scripts/telegram_curator.py
```
- Bot: @thebeakers_stem_bot
- Buttons: Quick Link, Rewrite, Editor's Pick, Skip
- Commands: /review, /status, /publish

### 3. AI Rewriting
```bash
python scripts/ai_rewriter.py test      # Test single article
python scripts/ai_rewriter.py rewrite chemistry 5  # Rewrite 5 chemistry articles
```
- Uses Ollama with qwen3:latest model
- Produces: Headline, Hook, Research, Why It Matters, Curriculum Connection, Key Terms, Difficulty, Mermaid Diagram, Audio Teaser, Think About
- Saves to `articles/[discipline]/[date]-[slug].json`

### 4. Index Generation
```bash
python scripts/generate_indexes.py
```
- Creates `articles/[discipline]/index.json` for each discipline

## Article Page Features

- **Mermaid.js diagrams** - Auto-rendered visual summaries
- **Audio player** - Browser SpeechSynthesis API (free TTS)
- **Curriculum connections** - Highlighted section linking to courses
- **Difficulty badges** - Freshman/Sophomore/Junior
- **Original source link** - Links back to research paper

## Planned Features

- [ ] Weekly podcasts
- [ ] Curated YouTube video playlists
- [ ] Pop-up definitions for key terms
- [ ] Search across all articles

## Contact

- **Founding Editor:** Kiran Boggavarapu
- **Email:** thebeakerscom@gmail.com
