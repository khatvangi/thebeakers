# The Beakers Content System

## Three-Lane Weekly Publishing

### Per Subject Per Week (Chem/Phys/Math/Eng/CS/Bio)
| Lane | Count | Read Time | Purpose |
|------|-------|-----------|---------|
| **In-Depth** | 1 | 8-15 min | Full explanation + curriculum bridge |
| **Digest** | 3-7 | 3-5 min | Claim + diagram + hook |
| **Blurbs** | 10-30 | 20-60 sec | TL;DR + course hook |

### Plus: 1 Education Highlight/week
Goal: Explain hard idea / Kill misconception / Show teaching move

---

## Scoring Rubric (0-5 each)

| Score | Meaning |
|-------|---------|
| **S - Significance** | 0=trivial, 3=removes bottleneck, 5=changes feasibility |
| **E - Evidence** | 0=weak, 3=solid controls, 5=multiple validations |
| **T - Teachability** | 0=can't explain, 3=with scaffolding, 5=ties to core concepts |
| **M - Media** | 0=no clean figure, 3=one pivot figure, 5=visually expressible |
| **H - Hype Penalty** | 0=honest, 5=breakthrough claims + thin methods |

### Routing Rules
```
In-Depth: E≥4 AND T≥4 AND (S≥4 OR M≥4) AND H≤2
Digest:   E≥3 AND T≥3 AND (S≥3 OR M≥3) AND H≤3
Blurb:    T≥2 AND (S≥3 OR M≥3), label "Frontier" if E≤2
Reject:   T≤1 OR (H≥4 AND E≤3)
```

---

## Content Templates

### In-Depth (8-15 min)
1. **One-sentence claim**: "This shows X using Y, matters because Z"
2. **Pivot figure**: what's plotted, what it proves, what it doesn't
3. **Mechanism in 3 steps**: A → B → C
4. **Curriculum bridge**: concept + derivation + limiting case
5. **Why doubt it**: failure mode / missing control
6. **Takeaway**: general idea students keep
7. **Mini-exercise**: 10-20 min task

### Digest (3-5 min)
- Claim + why it matters
- One diagram
- One curriculum hook
- One caution

### Blurb (20-60 sec)
- TL;DR (2 lines)
- Course hook (1 line)
- What to watch (1 line)

### Education Highlight
- Misconception (stated plainly)
- Why it feels true
- Why it's wrong (counterexample)
- Correct model (diagram/analogy)
- 10-minute classroom move
- 2-question exit check

---

## Curriculum Hooks (Required for ALL items)

**Concept hooks**: equilibrium, eigenvectors, diffusion, Fourier, control loops, Bayes, scaling laws, kinetics, thermodynamics, Maxwell, Schrodinger, Hardy-Weinberg

**Skill hooks**: order-of-magnitude estimate, interpret error bars, identify confounders, reproduce plot, dimensional analysis, back-of-envelope

---

## Data Schema

### Issue JSON (`content/issues/chemistry/2026-01-05.json`)
```json
{
  "subject": "chemistry",
  "week_of": "2026-01-05",
  "in_depth": ["note:indepth-chem-001"],
  "digest": ["note:digest-chem-001", "note:digest-chem-002"],
  "blurbs": ["note:blurb-chem-001"],
  "education_highlight": "note:edu-001"
}
```

### Note JSON (`content/notes/indepth-chem-001.json`)
```json
{
  "id": "indepth-chem-001",
  "type": "indepth",
  "subject": "chemistry",
  "slug": "solvent-cage-kinetics",
  "title": "Solvent-cage kinetics explained",
  "tldr": "Why reactions stall before they start",
  "difficulty": "intermediate",
  "course_hooks": ["kinetics", "diffusion"],
  "skill_hooks": ["interpret rate law"],
  "scores": { "S": 4, "E": 4, "T": 5, "M": 4, "H": 1 },
  "flags": { "peer_reviewed": true, "open_access": true, "frontier": false },
  "source": { "doi": "10.xxxx", "venue": "JACS", "published": "2026-01-02" }
}
```

---

## Collection Sources

### APIs (preferred over scraping)
- **OpenAlex**: Peer-reviewed OA literature with concept filters
- **arXiv**: Math/Physics/CS preprints
- **Europe PMC**: Life science OA
- **Unpaywall**: Verify OA + get PDF URLs

### RSS Feeds
- Nature Editors' Highlights
- Science/AAAS
- PNAS
- Subject-specific journals

### Education Journals (OA)
- Physical Review Physics Education Research
- Chemistry Education Research and Practice
- International Journal of STEM Education
- Journal of Microbiology & Biology Education

---

## Weekly Workflow

1. **Intake** (automated): Collect 200-800 candidates
2. **Triage** (30-60 min/subject): Score using rubric, route items
3. **Build** (2-4 hrs): In-depth first, then digest/blurbs
4. **Publish**: Push to site

---

## URL Structure

```
/chemistry/                        → latest issue
/chemistry/issues/2026-01-05/      → specific issue
/chemistry/indepth/<slug>/         → in-depth article
/chemistry/digest/<slug>/          → digest article
/chemistry/blurbs/                 → blurb list
/education/                        → education highlights
```
