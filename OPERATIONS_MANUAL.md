# TheBeakers Operations Manual

**Version:** v1.0-stable
**Date:** 2026-01-10
**Status:** Production Ready

---

## 1. System Overview

TheBeakers is an educational platform that rewrites cutting-edge research papers for undergraduate students, connecting findings to what they're learning in class.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         THEBEAKERS                               │
├─────────────────────────────────────────────────────────────────┤
│  DATA SOURCES                                                    │
│  ├── OA Feeds (arXiv, bioRxiv, PubMed, ChemRxiv...)            │
│  └── Secondary (ScienceDaily, MIT Tech Review → resolve DOI)    │
├─────────────────────────────────────────────────────────────────┤
│  PIPELINE (daily)                                                │
│  1. Collect feeds → seen_articles DB                            │
│  2. Secondary discovery → resolve to primary DOI                 │
│  3. Triage (S,E,T,M,H scoring) → route decision                 │
│  4. Fulltext fetch → PDF/HTML extraction                        │
│  5. Evidence upgrade → re-score with fulltext                   │
│  6. Select issue → pick daily quota                             │
│  7. Render → article_v2.html template                           │
│  8. Email → listmonk campaign                                   │
├─────────────────────────────────────────────────────────────────┤
│  SERVICES                                                        │
│  ├── Apache (port 80/443) → serves static site                  │
│  ├── Subscribe API (port 5050) → Flask/gunicorn                 │
│  ├── Listmonk (port 9000) → email campaigns                     │
│  └── Qdrant (port 6333) → curriculum vector search              │
├─────────────────────────────────────────────────────────────────┤
│  SCHEDULED                                                       │
│  ├── thebeakers-daily.timer → 6 AM daily                        │
│  └── thebeakers-weekly.timer → 8 AM Sundays                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
/storage/thebeakers/
├── index.html                    # Main landing page
├── article.html                  # Legacy article template
├── article-v2.html               # Current article template (v1.0)
├── subscribe/                    # Subscribe page
│   ├── index.html
│   └── subscribe.js
├── articles/                     # Generated article JSON
│   ├── biology/
│   ├── chemistry/
│   ├── physics/
│   ├── ai/
│   ├── engineering/
│   ├── mathematics/
│   └── agriculture/
├── deepdive/                     # Deep dive HTML pages
├── data/
│   └── articles.db               # SQLite database
├── config/
│   ├── feeds.yaml                # RSS feed sources
│   ├── listmonk_ids.json         # Listmonk list IDs
│   ├── curriculum_map.yaml       # Curriculum vocabulary
│   ├── thebeakers-daily.service  # Systemd daily service
│   ├── thebeakers-daily.timer    # Systemd daily timer
│   ├── thebeakers-weekly.service # Systemd weekly service
│   ├── thebeakers-weekly.timer   # Systemd weekly timer
│   ├── thebeakers-subscribe.service
│   └── apache-subscribe.conf     # Apache proxy config
├── scripts/
│   ├── run_daily_digest.py       # Daily pipeline orchestrator
│   ├── weekly_pipeline.py        # Weekly deep dive pipeline
│   ├── feed_collector_oa.py      # OA feed collector
│   ├── secondary_discovery.py    # Secondary source resolver
│   ├── triage.py                 # Article scoring/routing
│   ├── stage0_fulltext_fetch.py  # PDF extraction
│   ├── triage_evidence_upgrade.py
│   ├── select_weekly_issue.py
│   ├── setup_schedulers.sh       # Install systemd timers
│   └── email/
│       ├── subscribe_api.py      # Flask API
│       ├── send_campaign_listmonk.py
│       └── bootstrap_listmonk.py
├── templates/
│   └── article_v2.html           # Master template
├── public/
│   ├── css/
│   │   └── design-tokens.css     # Design system
│   └── js/
│       ├── quiz.js               # Quiz renderer
│       └── claims.js             # Claim ledger renderer
└── logs/
    ├── daily-digest.log
    └── weekly-deepdive.log
```

---

## 3. Database Schema

### seen_articles
```sql
CREATE TABLE seen_articles (
    url TEXT PRIMARY KEY,
    headline TEXT,
    discipline TEXT,
    source_type TEXT,         -- review | high_impact | education
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);
```

### archive
```sql
CREATE TABLE archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    headline TEXT,
    teaser TEXT,
    source TEXT,
    discipline TEXT,
    article_type TEXT,
    week TEXT,
    approved_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pdf_url TEXT,
    is_open_access INTEGER DEFAULT 1,
    oa_source TEXT,
    track TEXT,
    published_date TEXT,
    source_tier TEXT DEFAULT 'primary',    -- primary | secondary
    discovered_from TEXT,                   -- URL of secondary source
    primary_url TEXT,                       -- resolved DOI URL
    cadence TEXT,                           -- daily | bi_daily | weekly
    publish_at TEXT
);
```

---

## 4. Services

### 4.1 Subscribe API

**Location:** `/storage/thebeakers/scripts/email/subscribe_api.py`
**Port:** 5050
**Proxy:** Apache `/api/` → `http://127.0.0.1:5050/api/`

**Start/Stop:**
```bash
sudo systemctl start thebeakers-subscribe
sudo systemctl stop thebeakers-subscribe
sudo systemctl status thebeakers-subscribe
```

**Test:**
```bash
curl -X POST http://127.0.0.1:5050/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","cadence":"daily","subjects":["chemistry"]}'
```

**Environment Variables:**
- `LISTMONK_BASE_URL` = http://localhost:9000
- `LISTMONK_USER` = admin
- `LISTMONK_PASS` = spsdaily2026

### 4.2 Listmonk

**Port:** 9000
**Lists:**
- beakers_daily (ID: 7)
- beakers_weekly (ID: 8)
- beakers_education (ID: 9)

**Admin:** http://localhost:9000/admin

### 4.3 Daily Timer

**Service:** thebeakers-daily.service
**Timer:** thebeakers-daily.timer
**Schedule:** 6:00 AM daily (±15 min randomization)

**Commands:**
```bash
# check status
systemctl status thebeakers-daily.timer
systemctl list-timers thebeakers-*

# run manually
sudo systemctl start thebeakers-daily.service

# check logs
journalctl -u thebeakers-daily.service -f
tail -f /storage/thebeakers/logs/daily-digest.log
```

### 4.4 Weekly Timer

**Service:** thebeakers-weekly.service
**Timer:** thebeakers-weekly.timer
**Schedule:** Sundays 8:00 AM (±30 min randomization)

---

## 5. Pipeline Scripts

### 5.1 Daily Pipeline

**File:** `scripts/run_daily_digest.py`

**Usage:**
```bash
python scripts/run_daily_digest.py              # full run
python scripts/run_daily_digest.py --dry-run    # preview only
python scripts/run_daily_digest.py --skip-email # skip email step
```

**Steps:**
1. Collect OA feeds (limit 100)
2. Secondary discovery (limit 50)
3. Triage (limit 30)
4. Fulltext fetch (limit 20)
5. Evidence upgrade (limit 10)
6. Select daily issue
7. Render digest (TODO)
8. Send email (TODO)

### 5.2 Weekly Pipeline

**File:** `scripts/weekly_pipeline.py`

**Usage:**
```bash
python scripts/weekly_pipeline.py --status              # show status
python scripts/weekly_pipeline.py --subjects chemistry  # process one
python scripts/weekly_pipeline.py --build-deep chemistry # build HTML
```

### 5.3 Secondary Discovery

**File:** `scripts/secondary_discovery.py`

Scrapes secondary sources (ScienceDaily, MIT Tech Review) and resolves to primary DOIs.

**Patterns matched:**
- DOI: `10.xxxx/...`
- arXiv: `arxiv.org/abs/xxxx.xxxxx`
- PMCID: `pmc/articles/PMCxxxxxxx`

---

## 6. Templates

### 6.1 article_v2.html

**Location:** `/storage/thebeakers/templates/article_v2.html`
**Deployed:** `/storage/thebeakers/article-v2.html`

**Features:**
- Handles both `story[]` (Stage 1) and `panels[]` (Stage 2+) formats
- Claim ledger with evidence types
- Quiz with anti-hallucination feedback
- Curriculum connections
- Reading progress bar
- Accessible (keyboard nav, focus states, reduced motion)

**Usage:**
```
/article-v2.html?story=/path/to/story-data.json
```

### 6.2 story-data.json Schema

**v3 Schema Requirements:**

Stage 1 (truth extraction):
- `schema_version`: "v3"
- `paper_metadata`: {title, journal, year, doi, url}
- `paper_type`: string
- `research_question`: {text, pointers[]}
- `claim_ledger[]`: {id: C01-C25, type: QUOTE|PARAPHRASE|COMPUTED, claim, pointers[]}
- `structured_content`: {content_type, items[]}
- `story[]`: {text, supporting_claim_ids[]}
- `limitations[]`, `open_questions[]`, `missing_information[]`

Stage 2 (panelization):
- `panels[]`: {id: P01-P12, intent, label, narrative, claim_ids[], renderer}

Stage 3 (curriculum bridge):
- `curriculum_connections[]`: {id: CC01+, concept, subject, level, connection_type, boundary}

Stage 4 (quiz):
- `quiz[]`: {id: Q01+, type, prompt, options[], correct_index, evidence{claim_ids, panel_ids, curriculum_concept}, anti_hallucination}

---

## 7. Validation

**Validator:** `/home/kiran/.claude/skills/story-renderer/scripts/validate_story_data.py`

**Usage:**
```bash
python validate_story_data.py /path/to/story-data.json 1  # Stage 1
python validate_story_data.py /path/to/story-data.json 4  # Full (Stage 4)
```

---

## 8. Troubleshooting

### Subscribe API not responding
```bash
# check if running
systemctl status thebeakers-subscribe

# check logs
journalctl -u thebeakers-subscribe -n 50

# restart
sudo systemctl restart thebeakers-subscribe

# test directly
curl http://127.0.0.1:5050/api/health
```

### Listmonk 409 Conflict
Subscriber already exists. The API handles this by updating existing subscribers.

### Timer not running
```bash
# check timer status
systemctl list-timers thebeakers-*

# check if service failed
journalctl -u thebeakers-daily.service --since today

# re-enable timer
sudo systemctl enable --now thebeakers-daily.timer
```

### Article not rendering
1. Check story-data.json exists at specified path
2. Validate JSON syntax: `python -m json.tool story-data.json`
3. Validate schema: `python validate_story_data.py story-data.json 1`
4. Check browser console for JS errors

### Database locked
```bash
# check for processes
fuser /storage/thebeakers/data/articles.db

# if safe, kill and retry
```

---

## 9. Backup & Restore

### Backup
```bash
# database
cp /storage/thebeakers/data/articles.db /storage/thebeakers/data/articles.db.backup.$(date +%Y%m%d)

# config
tar -czvf thebeakers-config-$(date +%Y%m%d).tar.gz /storage/thebeakers/config/

# full site
tar -czvf thebeakers-full-$(date +%Y%m%d).tar.gz /storage/thebeakers/
```

### Restore
```bash
# database
cp /storage/thebeakers/data/articles.db.backup.YYYYMMDD /storage/thebeakers/data/articles.db

# restart services
sudo systemctl restart thebeakers-subscribe
```

---

## 10. Current State (2026-01-10)

### Database
- 105 articles in archive (74 primary, 31 with secondary resolution)
- 7 pending deep dives

### Services
- Subscribe API: Running ✓
- Daily timer: Active, next run 2026-01-11 06:10 AM
- Weekly timer: Active, next run 2026-01-11 08:04 AM

### Listmonk Lists
- beakers_daily: ID 7
- beakers_weekly: ID 8
- beakers_education: ID 9

### TODO (render/email)
- `render_digest_page.py` not implemented
- Daily email send not implemented
- Need home page + index pages

---

## 11. Quick Commands

```bash
# check all services
systemctl status thebeakers-subscribe
systemctl list-timers thebeakers-*

# manual pipeline run (dry)
cd /storage/thebeakers
python scripts/run_daily_digest.py --dry-run

# validate story-data
python /home/kiran/.claude/skills/story-renderer/scripts/validate_story_data.py \
  /storage/visual-stories/graphical-abstracts-rules/story-data.json 1

# view logs
tail -f /storage/thebeakers/logs/daily-digest.log
journalctl -u thebeakers-daily.service -f

# test subscribe
curl -X POST http://127.0.0.1:5050/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","cadence":"daily"}'

# database queries
sqlite3 /storage/thebeakers/data/articles.db "SELECT COUNT(*) FROM archive"
sqlite3 /storage/thebeakers/data/articles.db "SELECT discipline, COUNT(*) FROM archive GROUP BY discipline"
```

---

## 12. Contacts & Resources

- **Site:** https://thebeakers.com
- **GitHub:** https://github.com/khatvangi/thebeakers
- **Email:** thebeakerscom@gmail.com
- **Listmonk Admin:** http://localhost:9000/admin

---

*Generated: 2026-01-10 | Version: v1.0-stable*
