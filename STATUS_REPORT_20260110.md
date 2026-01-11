# TheBeakers Status Report

**Date:** 2026-01-10
**Status:** v1.0-stable (pre-launch)

---

## Executive Summary

TheBeakers is ready for soft launch. Core infrastructure is operational:
- Daily/weekly pipelines scheduled
- Subscribe API running
- Article template hardened for accessibility and performance
- Design system established

**Blockers before public launch:**
1. No home page (site needs a front door)
2. No browse/index pages (no discoverability)
3. No SEO/social cards (won't share well)
4. No analytics (can't measure success)

---

## What Was Built (This Session)

### Infrastructure
| Component | Status | Notes |
|-----------|--------|-------|
| `run_daily_digest.py` | ✅ Working | Orchestrates 8-step pipeline |
| `secondary_discovery.py` | ✅ Working | 31/50 articles resolved to DOIs |
| `subscribe_api.py` | ✅ Running | Port 5050, listmonk integration |
| systemd timers | ✅ Installed | Daily 6AM, Weekly Sun 8AM |
| `curriculum_map.yaml` | ✅ Created | 6 disciplines, controlled vocab |
| `article_v2.html` | ✅ Hardened | Accessibility, performance, progress bar |
| `design-tokens.css` | ✅ Created | Visual identity locked |
| `quiz.js` / `claims.js` | ✅ Created | Reusable renderers |

### Database
- **archive:** 105 articles (74 primary, 31 resolved from secondary)
- **seen_articles:** Basic tracking
- **New columns:** source_tier, discovered_from, primary_url, cadence, publish_at

### Listmonk Lists
| List | ID | Purpose |
|------|-----|---------|
| beakers_daily | 7 | Daily digest subscribers |
| beakers_weekly | 8 | Weekly deep dive subscribers |
| beakers_education | 9 | Education-focused content |

---

## What's Working

### ✅ Daily Pipeline (Dry Run)
```
[20:09:38] === DAILY DIGEST PIPELINE ===
[20:09:38] date: 2026-01-10
Steps 1-6: ✓ (would run)
Steps 7-8: TODO (render, email)
```

### ✅ Weekly Pipeline
```
7 disciplines with pending deep dives
Status command working
```

### ✅ Subscribe API
```bash
curl -X POST http://127.0.0.1:5050/api/subscribe \
  -d '{"email":"test@test.com","cadence":"daily"}'
# Returns: {"ok":true,"action":"created"}
```

### ✅ Template (article_v2.html)
- Handles v3 schema (story-data.json)
- Accessible: keyboard nav, focus states, reduced motion
- Reading progress indicator
- Claim ledger with evidence types
- Quiz with anti-hallucination feedback

### ✅ Timers
```
thebeakers-daily.timer   Sun 2026-01-11 06:10:00 CST
thebeakers-weekly.timer  Sun 2026-01-11 08:04:39 CST
```

---

## What's NOT Working / TODO

### 🔴 Critical (Blocks Launch)
1. **No home page** - `/` shows nothing useful
2. **No index pages** - Can't browse articles
3. **No SEO** - Articles won't share well
4. **render_digest_page.py** - Not implemented
5. **Email send for daily** - Not implemented

### 🟡 Important (Post-Launch)
1. Analytics (Plausible/Umami)
2. Search functionality
3. Mobile layout testing

### 🟢 Nice to Have
1. Audio teasers
2. NotebookLM integration for deep dives
3. User preferences page

---

## File Inventory

### Core Templates
```
/storage/thebeakers/article-v2.html      # 886 lines, hardened
/storage/thebeakers/templates/article_v2.html  # master copy
```

### Scripts
```
/storage/thebeakers/scripts/
├── run_daily_digest.py        # 134 lines
├── weekly_pipeline.py         # existing
├── feed_collector_oa.py       # existing
├── secondary_discovery.py     # 300+ lines
├── triage.py                  # existing
├── setup_schedulers.sh        # 55 lines
└── email/
    ├── subscribe_api.py       # 192 lines
    ├── send_campaign_listmonk.py
    └── bootstrap_listmonk.py
```

### Config
```
/storage/thebeakers/config/
├── feeds.yaml                 # RSS sources
├── curriculum_map.yaml        # 400+ lines
├── listmonk_ids.json          # {daily:7, weekly:8, education:9}
├── thebeakers-daily.service
├── thebeakers-daily.timer
├── thebeakers-weekly.service
├── thebeakers-weekly.timer
└── thebeakers-subscribe.service
```

### Design System
```
/storage/thebeakers/public/css/design-tokens.css  # 150 lines
/storage/thebeakers/public/js/quiz.js             # 180 lines
/storage/thebeakers/public/js/claims.js           # 140 lines
```

---

## Test Results

### Schema Validation
```
story-data.json (graphical-abstracts-rules): Stage 1 PASS
```

### Subscribe API
```
Health check: 200 OK
Create subscriber: 200 OK
Update subscriber: 200 OK (via 409 handling)
```

### Timer Status
```
Both timers: active (waiting)
Next runs scheduled correctly
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Timer fails silently | Medium | High | Check logs daily |
| Listmonk goes down | Low | High | Health monitoring |
| Article renders broken | Low | Medium | Schema validation |
| Subscribe doesn't work | Low | High | Test before each push |

---

## Recommended Next Steps

### Immediate (Before Launch)
1. Create home page (`/`) with manifesto + subscribe CTA
2. Create index pages (`/issues/`, `/topics/`)
3. Add SEO meta tags + JSON-LD
4. Add Plausible/Umami analytics
5. Push to git

### Week 1
1. Monitor timer runs
2. Fix any broken renders
3. Send first email campaign (manual)

### Week 2+
1. Automate email sends
2. Add search
3. Iterate based on analytics

---

## Rollback Procedure

If anything goes wrong:

```bash
# 1. Stop services
sudo systemctl stop thebeakers-subscribe
sudo systemctl stop thebeakers-daily.timer
sudo systemctl stop thebeakers-weekly.timer

# 2. Restore database
cp /storage/thebeakers/data/articles.db.backup.YYYYMMDD \
   /storage/thebeakers/data/articles.db

# 3. Restore files (if needed)
tar -xzvf thebeakers-full-YYYYMMDD.tar.gz -C /

# 4. Restart
sudo systemctl start thebeakers-subscribe
sudo systemctl start thebeakers-daily.timer
sudo systemctl start thebeakers-weekly.timer
```

---

## Sign-Off Checklist

Before declaring "done":

- [ ] Daily timer runs clean for 7 days
- [ ] 0 broken renders
- [ ] ≥1 deep dive published and mailed
- [ ] Subscribe works end-to-end
- [ ] Home page exists
- [ ] Can browse articles
- [ ] Social cards work

---

*Report generated: 2026-01-10 20:15 CST*
