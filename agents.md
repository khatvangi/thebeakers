# Claude-code agents (delta to current repo)

## note
These agents must reuse existing code and templates.
No new HTML templates. No prompt rewrites.

---

## agent: feed_ingestor
uses:
- scripts/feed_collector.py

does:
- collect candidates into data/pending_articles.json

output:
- data/pending_articles.json (existing)

---

## agent: access_resolver (new, small)
does:
- for each candidate with DOI or URL:
  - determine access_level:
    oa_pdf | accepted_ms | preprint | metadata_only
- never scrape paywalls

output:
- data/resolution.json (new)

---

## agent: scorer (new, small)
does:
- compute value and feasibility scores using metadata + access_level
- apply thresholds
- assign:
  review_status
  publish_label

output:
- data/shortlist.json (new)

---

## agent: writer_existing (existing)
uses:
- scripts/ai_rewriter.py

does:
- produce regular articles json for your categories

output:
- articles/<discipline>/*.json (existing)

---

## agent: explain_builder (existing template constraint)
uses:
- deepdive/solar-cell-bromine-story.html
- deepdive/solar-cell-bromine-visual.html
- /storage/napkin/prompts/explain-story.txt
- /storage/napkin/prompts/explain-visual.txt

does:
- generate explain pages from shortlist items
- must insert credibility badge text

output:
- explain/*.html (existing structure)

---

## agent: validator (new, small)
does:
- check:
  - credibility badge present (peer-reviewed vs preprint)
  - if preprint, include “provisional” language in a fixed sentence
  - if missing OA/fulltext, do not publish as explain/deepdive

output:
- a pass/fail report in data/validation.json

