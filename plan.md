# The Beakers — intake + explain/deepdive workflow (delta plan v1)

## goal
Add a rigor-first intake and labeling layer without rewriting existing scripts/templates.

## do not change
- deepdive templates (solar-cell-bromine*.html)
- napkin prompt files in /storage/napkin/prompts/*
- existing site structure (articles/*, explain/*, deepdive/*)
- existing scripts unless a small patch is required

## new components (additive)
- config/sources.yaml: canonical intake sources (feeds + labs)
- a lightweight "resolver + scorer" step that writes a shortlist JSON
- optional StorySpec JSON only for deepdive/explain pages (not for all articles yet)

## phase 0 — drop-in configs (1 hour)
1) create config/ directory
2) add config/sources.yaml (labs + feeds)
3) add plan.md, agents.md, skills.md (this doc set)

## phase 1 — keep current weekly pipeline, add a “shortlist” output (small change)
current:
- scripts/feed_collector.py → data/pending_articles.json
- scripts/ai_rewriter.py → articles/<discipline>/*.json
- scripts/generate_indexes.py → index.json files

add:
- scripts/weekly_pipeline.py (or a new tiny script) produces:
  data/shortlist.json with:
  - candidate_id
  - doi/url
  - review_status: peer_reviewed|preprint|unknown
  - publish_label: Peer-Reviewed|Frontier (Preprint)
  - access_level: oa_pdf|accepted_ms|preprint|metadata_only
  - scores: value, feasibility

## phase 2 — credibility labeling (no template rewrite)
rule:
- all explain/deepdive pages must display a badge:
  - Peer-Reviewed
  - Frontier (Preprint)
- regular article.json can store the label and article.html can display it (optional)

## phase 3 — deepdive/explain generation uses “truth-first” prompts (additive)
do not replace your existing napkin prompts yet.
instead:
- for deepdive/explain only:
  produce a structured truth object first (claim ledger)
  then feed that into the existing explain-story / explain-visual prompts as input context

outputs remain:
- deepdive/<slug>-story.html
- deepdive/<slug>-visual.html
- explain/<discipline>-<doi>.html

## phase 4 — gradually expand labs-first
start with 10–20 labs.
monthly:
- add 2–3 labs per domain based on which papers you actually publish and like.

## definition of done (v1)
- shortlist exists with access+credibility labels
- explain/deepdive pages show credibility badge
- deepdive/explain claims are traceable to the source PDF

