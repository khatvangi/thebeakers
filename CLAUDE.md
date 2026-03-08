# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# The Beakers

STEM research rewritten for undergraduate students. Cutting-edge research translated into language students can understand, connected to what they're learning in class.

**Live site:** https://thebeakers.com
**Repo:** https://github.com/khatvangi/thebeakers
**Hosting:** Cloudflare Pages (auto-deploy from GitHub push)
**Motto:** व्यये कृते वर्धत एव नित्यं — "Knowledge always grows when shared"

## Approach

Keep things SIMPLE. Strive for simplicity, clarity and brevity in code.

- Don't jump into writing code — DISCUSS the approach FIRST, critique it, then pick the best path
- Do not be overly optimistic: TRUTH and ROOT CAUSE matter more than feel-good answers
- Write code ONLY when asked. Small fixes are fine, but don't write large chunks unprompted
- Think analytically and critically — the goal is a working solution, not agreement
- If data/code is available, don't guess the root cause — analyze and find it
- Divide and conquer: break down → solve each part → combine

### Coding Style
- Keep solutions SIMPLE without sacrificing functionality
- Never capitalize comments
- Prefer descriptive function names: `findMeaning` over `getMeaning`
- When a simple update is needed, don't rewrite the whole file
- Don't update documentation/file headers for small fixes — just comment where the change is made

### When Showing Code Changes
1. Show the previous couple of lines before the change
2. Mark changes with `## CHANGE NEEDED HERE`
3. Show a couple of lines after with `## CHANGE ENDS HERE`

---

## Architecture Overview

### Three-Lane Content System

Every discipline publishes weekly across three lanes:

| Lane | Count/Week | Read Time | Routing Rule |
|------|-----------|-----------|--------------|
| **In-Depth** | 1 | 8-15 min | E≥4, T≥4, (S≥4 OR M≥4), H≤2 |
| **Digest** | 3-7 | 3-5 min | E≥3, T≥3, (S≥3 OR M≥3), H≤3 |
| **Blurbs** | 10-30 | 20-60 sec | T≥2, (S≥3 OR M≥3); "Frontier" if E≤2 |

Scores: **S**(ignificance), **E**(vidence), **T**(eachability), **M**(edia affordance), **H**(ype penalty) — each 0-5.

### Daily Pipeline (automated, 6 AM UTC)

Orchestrated by `scripts/run_daily_digest.py`:

```
1. Collect      → feed_collector.py + secondary_discovery.py + openalex_discovery.py
2. Triage       → triage.py (2-model committee: qwen3 builder + gemma2 skeptic)
3. Fetch PDF    → stage0_fulltext_fetch.py (Unpaywall → PMC → direct DOI)
4. Evidence     → triage_evidence_upgrade.py (re-score E/H with fulltext)
5. Select       → select_weekly_issue.py (quota per discipline)
6. Render       → render_digest_page.py → data/digest_YYYY-MM-DD.html
7. Email        → scripts/email/send_campaign_listmonk.py
```

### Services

| Service | Port | Purpose |
|---------|------|---------|
| Apache | 80/443 | Static site |
| Subscribe API | 5050 | Flask/gunicorn newsletter signup |
| Listmonk | 9000 | Email campaigns |
| Qdrant | 6333 | Curriculum vector search |

### Systemd Timers

| Timer | Schedule | Script |
|-------|----------|--------|
| `thebeakers-daily.timer` | 6 AM UTC daily | `run_daily_digest.py` |
| `thebeakers-weekly.timer` | 8 AM UTC Sundays | `weekly_pipeline.py` |

Config files in `config/` — install with `systemctl --user`.

---

## Key Commands

### Daily Pipeline
```bash
python scripts/run_daily_digest.py              # full daily pipeline
python scripts/feed_collector.py                 # collect from RSS feeds
python scripts/openalex_discovery.py             # OpenAlex API discovery
python scripts/secondary_discovery.py            # secondary news → primary DOI
python scripts/triage.py                         # run 2-model scoring committee
python scripts/stage0_fulltext_fetch.py          # fetch PDFs via Unpaywall/PMC
python scripts/triage_evidence_upgrade.py        # re-score with fulltext
python scripts/select_weekly_issue.py            # pick weekly quota
python scripts/render_digest_page.py             # render digest HTML
```

### Weekly Deep Dives
```bash
python scripts/weekly_pipeline.py                # full weekly pipeline
python scripts/story_generator.py                # generate visual stories from PDFs
python scripts/batch_visual_stories.py           # bulk visual story generation
python scripts/generate_indexes.py               # regenerate article index files
```

### Curriculum System
```bash
python scripts/curriculum_pipeline.py chemistry  # fetch → match → quiz for discipline
python scripts/curriculum_pipeline.py --all      # all disciplines
python scripts/curriculum_matcher.py --test      # test paper→curriculum matching
python scripts/quiz_generator.py chemistry kinetics
python scripts/knowledge_graph_builder.py        # rebuild D3.js knowledge graphs
python scripts/update_discipline_curriculum.py   # sync pages with curriculum.json
```

### Content Agents (run from /storage/agents/)
```bash
cd /storage/agents
python cli.py deepdive thebeakers -d chemistry   # collect review articles
python cli.py education thebeakers -d all         # education journal papers
python cli.py concept thebeakers -t atomic-structure -d chemistry
python cli.py media thebeakers -d physics         # curate YouTube videos
```

### Email
```bash
python scripts/email/send_campaign_listmonk.py   # send digest campaign
python scripts/email/bootstrap_listmonk.py       # initialize Listmonk
```

### Publishing
```bash
git add . && git commit -m "Weekly update YYYY-MM-DD" && git push
# Cloudflare Pages auto-deploys from GitHub push
```

---

## Database (SQLite)

**Path:** `data/articles.db`

### Key Tables

| Table | Purpose |
|-------|---------|
| `triage_run` | Batch metadata (run_id, week_of, model versions) |
| `triage_result` | Final routing (S,E,T,M,H scores, route, access_state, fulltext_ok) |
| `model_vote` | Raw builder/skeptic model outputs |
| `issue` | Weekly selections (week_of, discipline, slot, rank_score) |
| `archive` | Published articles (approved_date, oa_source, track) |
| `seen_articles` | Dedup tracking (url, headline, first_seen, status) |
| `deepdive_candidates` | Papers pending deep dive treatment |
| `education_papers` | Education journal papers |
| `media_items` | Curated YouTube videos (70+) |

---

## DO NOT REINVENT — USE EXISTING CODE

**CRITICAL: Always use existing scripts and templates. Never create new ones from scratch.**

### Canonical Templates (LOCKED — DO NOT MODIFY)

| Purpose | File | Best For |
|---------|------|----------|
| Deep Dive | `deepdive/solar-cell-bromine.html` | Full NotebookLM treatment |
| **Visual Summary** | `deepdive/solar-cell-bromine-visual.html` | Quick overview, data-heavy |
| **Detailed Story** | `deepdive/solar-cell-bromine-story.html` | Complex concepts, step-by-step |

### Canonical Prompts (LOCKED — DO NOT MODIFY)

| Format | Prompt File |
|--------|-------------|
| Visual Summary | `/storage/napkin/prompts/explain-visual.txt` |
| Detailed Story | `/storage/napkin/prompts/explain-story.txt` |
| TL;DR | `/storage/napkin/prompts/tldr.txt` |

### Rules
1. **NEVER** create new HTML templates — copy solar-cell-bromine-*.html
2. **NEVER** modify the locked templates or prompts
3. **ALWAYS** use one of the two explain formats (Visual or Story)
4. **ALWAYS** copy CSS/styling exactly from the canonical templates
5. **ALWAYS** check existing code before writing new code

### Visual Summary Format
Quick visual overview with cards, grids, progress bars. NO Mermaid.
- Hero with 3 key stats → Challenge cards → Research Question → Comparison → Mechanism grid → Results timeline → Key Insight
- Elements: Lucide icons, visual-card grid, comparison cards, mechanism-grid, timeline-bars, insight-box

### Detailed Story Format
8-scene narrative with Mermaid diagrams.
- Challenge → Hypothesis → Experiment → Method → Results → Explanation → Achievement → Implication
- Elements: Mermaid diagrams (mindmap, flowchart, timeline), highlight-box, stats-grid

### TL;DR Format
One sentence (max 2). Active voice, simple words, concrete benefit, no citations. Plain text only.

---

## Triage System (2-Model Committee)

The scoring pipeline uses two Ollama models in sequence:
1. **Builder** (qwen3:latest): Generates S,E,T,M,H scores + metadata
2. **Skeptic** (gemma2:9b): Challenges scores, especially Evidence and Hype

Cached responses in `cache/llm/` keyed by `{model}_{role}_{hash}.json`.

Routing: indepth → digest → blurb → reject (see routing rules above).
Articles with E≤2 get `frontier_flag=1` and labeled "Frontier (Preprint)".

---

## Qdrant + Curriculum Integration (SIGNATURE FEATURE)

Every article connects to undergraduate curriculum via Qdrant vector search.

```
Qdrant (localhost:6333)
├── chunks_text (9,884 points) — LibreTexts textbooks (665 books)
├── quizzes_questions — Quiz bank
└── chunks_hybrid — Hybrid search
```

**Data:** `data/curriculum.json` — 7 disciplines, 35 subfields, 142 topics with keywords.
**Graphs:** `data/graphs/[discipline]_graph.json` — D3.js knowledge graph data (142 topics, 390 books, 1,105 edges).
**Explorer:** `/explore/` — Interactive D3.js force-directed graph.

### Difficulty Levels
| Level | Course | LibreTexts Category |
|-------|--------|---------------------|
| Freshman | 100-200 | Introductory, General |
| Sophomore | 200-300 | Organic, Intermediate |
| Junior | 300-400 | Physical, Analytical, Advanced |

---

## Design System

### Theme
- Dark background (#0f172a), card-based layout
- Plus Jakarta Sans + Instrument Serif fonts

### Color Palette
```css
--bg-dark: #0f172a;
--bg-card: #1e293b;
--accent-green: #10b981;  /* Natural Sciences */
--accent-blue: #3b82f6;   /* Technology */
--accent-orange: #f59e0b; /* Engineering */
--accent-purple: #8b5cf6; /* Mathematics */
--accent-cyan: #06b6d4;   /* Deep Dive accent */
```

### Disciplines
Natural Sciences: Biology, Chemistry, Physics, Agriculture
Technology: Artificial Intelligence
Engineering: Engineering (Civil, Mechanical, Electrical, Chemical)
Mathematics: Mathematics

---

## Key Directories

```
config/               # systemd timers, feeds.yaml, curriculum_map.yaml, listmonk_ids.json
scripts/              # all pipeline scripts (35+)
scripts/email/        # Listmonk email: send, bootstrap, subscribe API
data/articles.db      # SQLite database (core state)
data/papers/          # downloaded PDFs organized by DOI/discipline
data/digest_*.html    # rendered daily digest pages
data/stories/         # generated story data
data/graphs/          # D3.js knowledge graph JSON
data/curriculum.json  # 7 disciplines, 142 topics
cache/llm/            # triage model response cache
cache/unpaywall/      # Unpaywall API response cache
deepdive/             # deep dive HTML pages (static, rich media)
concepts/             # visual concept explainers (Lucide icons, cards)
explore/              # interactive knowledge graph explorer (D3.js)
articles/             # generated article JSON + index files per discipline
```

---

## Deployment

- **Hosting:** Cloudflare Pages (project: `thebeakers`)
- **DNS:** Cloudflare proxy → Pages (NOT the Cloudflare Tunnel on this machine)
- **GitHub auto-deploy is BROKEN** — Vercel webhook intercepts and fails
- **Manual deploy required:**
  ```bash
  # move >25MB files first (Cloudflare Pages limit)
  mv solar/*.m4a /tmp/ && mv solar/*.mp4 /tmp/
  mv deepdive/solar-cell-bromine/video.mp4 /tmp/ && mv deepdive/solar-cell-bromine/podcast.m4a /tmp/

  export CLOUDFLARE_API_TOKEN="<token>"
  export CLOUDFLARE_ACCOUNT_ID="fc52021d8b580a3b3ddcd6f22c730eb3"
  npx wrangler pages deploy /storage/thebeakers --project-name=thebeakers --commit-dirty=true

  # restore files after deploy
  mv /tmp/*.m4a solar/ && mv /tmp/*.mp4 solar/
  mv /tmp/video.mp4 deepdive/solar-cell-bromine/ && mv /tmp/podcast.m4a deepdive/solar-cell-bromine/
  ```
- **Media:** Podcasts → SoundCloud, Videos → YouTube (25MB file limit)
- **Related:** spsdaily.thebeakers.com, newsletter.thebeakers.com (Listmonk)
- **Cloudflare Tunnel** runs on this machine (port 80/Apache) but DNS does NOT point to it for thebeakers.com

### NotebookLM Deep Dives (MCP integration)

Automated via `scripts/process_indepth.py` (requires Claude Code with NotebookLM MCP):

```bash
python scripts/process_indepth.py --list                    # show candidates
python scripts/process_indepth.py --prepare <article_url>   # setup + print MCP steps
python scripts/process_indepth.py --build-html <article_url> # generate HTML from assets
```

MCP workflow: `notebook_create` → `source_add` (PDF) → `studio_create` (audio/video/report/quiz) → poll `studio_status` → `download_artifact` → `--build-html`

Assets stored in `deepdive/<doi-slug>/` (audio.mp4, quiz.json, report.md).
Note: `download_artifact` may fail for some types — use `notebook_query` for reports, `curl` audio URL from `studio_status`.

## Key Config Files

- `config.yaml` — credibility policy, feed definitions, resolution ladder
- `config/feeds.yaml` — (if present) additional feed config
- `config/curriculum_map.yaml` — 7 disciplines, 35 subfields, 142 topics with prerequisites
- `config/listmonk_ids.json` — Listmonk segment mappings
- `CONTENT_SYSTEM.md` — detailed scoring rubric, content templates, URL structure
- `OPERATIONS_MANUAL.md` — full operations reference (v1.0-stable, Jan 2026)
