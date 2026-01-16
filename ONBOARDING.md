# The Beakers - LLM Onboarding Report

**Last Updated:** 2026-01-16
**Status:** Pre-announcement (student launch Monday 2026-01-20)

## Quick Context

**What:** STEM research rewritten for undergraduates. Papers translated to student-friendly language with curriculum connections.

**Live URL:** https://thebeakers.com

**Motto:** "Knowledge always grows when shared" (Chanakya Niti)

---

## Current State (Jan 16, 2026)

### Content Published
| Type | Count | Location |
|------|-------|----------|
| Articles | 21 (3 per discipline) | `articles/<discipline>/*.json` |
| Explain pages | 47 | `explain/*.html` |
| Deep Dives | 6 | `deepdive/*.html` |
| Archive (DB) | 105 articles | `data/articles.db` |

### Infrastructure Status
| Component | Status | Notes |
|-----------|--------|-------|
| Weekly pipeline | Working | `scripts/weekly_pipeline.py` |
| Feed collection | Working | 47 journal RSS feeds |
| Explain generation | Working | Uses locked templates |
| Subscribe API | Working | Port 5050, Listmonk integration |
| Systemd timers | Installed | Daily 6AM, Weekly Sun 8AM |
| **Daily digest render** | **NOT DONE** | Step 7 of `run_daily_digest.py` |
| **Email automation** | **NOT DONE** | Step 8 of `run_daily_digest.py` |

### 7 Disciplines
Chemistry, Physics, Biology, Mathematics, Engineering, AI, Agriculture

---

## Key Files Quick Reference

### Templates (LOCKED - DO NOT MODIFY)
```
deepdive/solar-cell-bromine-visual.html  # visual summary template
deepdive/solar-cell-bromine-story.html   # narrative template
/storage/napkin/prompts/explain-visual.txt
/storage/napkin/prompts/explain-story.txt
/storage/napkin/prompts/tldr.txt
```

### Pipeline Scripts
```
scripts/weekly_pipeline.py       # main weekly orchestration (57KB)
scripts/run_daily_digest.py      # daily pipeline (INCOMPLETE)
scripts/feed_collector_oa.py     # open access collection
scripts/triage.py                # SETMH scoring
scripts/secondary_discovery.py   # DOI resolution
scripts/stage0_fulltext_fetch.py # PDF extraction
```

### Configuration
```
config/sources.yaml      # feed sources and credibility policy
config/feeds.yaml        # RSS feed URLs by discipline
scripts/feeds.yaml       # alternative feed config
```

### Database
```
data/articles.db         # SQLite - seen_articles, archive tables
```

### Email/Subscribe
```
scripts/email/subscribe_api.py      # Flask API (port 5050)
scripts/email/send_campaign_listmonk.py
config/listmonk_ids.json            # list IDs
```

---

## Common Tasks

### Generate Explain Article
```bash
# uses /storage/napkin/src/explain_generator.py
# copies template from deepdive/solar-cell-bromine-*.html
python scripts/weekly_pipeline.py
```

### Run Weekly Pipeline
```bash
python scripts/weekly_pipeline.py
# collects from high-impact journals
# scores and routes articles
# generates explain HTML
```

### Run Daily Digest (INCOMPLETE)
```bash
python scripts/run_daily_digest.py
# Steps 1-6 work, Steps 7-8 TODO
```

### Check Feed Collection
```bash
python scripts/feed_collector_oa.py
```

### Database Queries
```bash
sqlite3 data/articles.db "SELECT COUNT(*) FROM archive;"
sqlite3 data/articles.db "SELECT discipline, COUNT(*) FROM archive GROUP BY discipline;"
```

---

## Architecture Overview

```
RSS Feeds (47 sources)
       |
       v
feed_collector_oa.py --> pending_articles.json
       |
       v
   triage.py (SETMH scoring)
       |
       +---> in_depth (weekly deep dives)
       +---> digest (explain pages)
       +---> blurb (TL;DR only)
       +---> reject
       |
       v
weekly_pipeline.py --> explain/*.html
                   --> articles/<discipline>/*.json
```

### Three Content Lanes
1. **In-Depth** (1/week/subject): Full NotebookLM treatment - podcast, video, quiz
2. **Digest** (3-7/week/subject): Visual or story explain pages
3. **Blurbs** (10-30/week/subject): TL;DR one-liners

### SETMH Scoring
- **S**ignificance: 0-5
- **E**vidence: 0-5
- **T**eachability: 0-5
- **M**edia affordance: 0-5
- **H**ype penalty: 0-5

---

## Guardrails (DO NOT)

1. **NEVER** modify locked templates or prompts
2. **NEVER** bypass paywalls or use mirrors
3. **NEVER** invent claims not in source PDF
4. **NEVER** create new HTML templates (copy existing)
5. **ALWAYS** label content: "Peer-Reviewed" or "Frontier (Preprint)"
6. **ALWAYS** use existing scripts before writing new ones

---

## Known Gaps (Priority Order)

### Critical for Launch
1. Daily digest rendering (`run_daily_digest.py` Step 7)
2. Email send automation (`run_daily_digest.py` Step 8)

### Nice to Have
3. Search functionality
4. Analytics integration
5. Audio teasers

---

## Deployment

- **Hosting:** Cloudflare Pages (auto-deploy from GitHub)
- **Repo:** github.com/khatvangi/thebeakers
- **Domain:** thebeakers.com (Cloudflare DNS)
- **Media:** SoundCloud (audio), YouTube (video)

### Deploy Process
```bash
git add . && git commit -m "message" && git push
# Cloudflare auto-deploys on push to main
```

---

## External Integrations

| Service | Purpose | Config Location |
|---------|---------|-----------------|
| Listmonk | Email lists | localhost:9000, `config/listmonk_ids.json` |
| SoundCloud | Podcast hosting | Manual upload |
| YouTube | Video hosting | Manual upload |
| NotebookLM | Deep dive generation | notebooklm.google.com |
| OpenAlex | Article metadata | `scripts/openalex_discovery.py` |

---

## Session Checklist for LLM

When starting a new session:

1. Read this file (`ONBOARDING.md`)
2. Check `git status` for uncommitted work
3. Check `data/articles.db` for current content count
4. Review `CLAUDE.md` for coding guidelines
5. Ask user what task to focus on

---

## Contact

- **Editor:** Kiran Boggavarapu
- **Email:** thebeakerscom@gmail.com
