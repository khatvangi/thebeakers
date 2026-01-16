# skills + guardrails (v1)

## allowed
- collect metadata from RSS/TOC/lab pages
- download PDFs only when:
  - open access publisher
  - repository/accepted manuscript
  - preprint servers
  - PMC
- generate:
  - regular article json (your existing format)
  - explain/deepdive HTML by copying canonical templates

## forbidden (automation)
- bypassing paywalls
- using mirrors
- inventing mechanisms/claims not in the PDF
- removing limitations to make story smoother

## credibility rules
- every explain/deepdive output must be labeled:
  Peer-Reviewed | Frontier (Preprint)
- preprints must include a fixed disclaimer sentence:
  "This is a preprint and has not yet been peer reviewed."

## minimalism rule
- prefer small patches to existing scripts
- never create new HTML templates
- never modify locked prompts/templates

