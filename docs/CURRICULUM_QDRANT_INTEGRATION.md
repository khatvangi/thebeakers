# Curriculum Connection & Quiz System

**The Beakers' Signature Feature** - What differentiates us from other science news sites.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        QDRANT (localhost:6333)                  │
├─────────────────────────────────────────────────────────────────┤
│  chunks_text (9,884 points)                                     │
│  └── LibreTexts textbooks (665 books)                           │
│      ├── chemistry (Intro, General, Organic, Physical, etc.)    │
│      ├── physics                                                │
│      ├── biology                                                │
│      ├── math                                                   │
│      ├── engineering                                            │
│      └── statistics                                             │
├─────────────────────────────────────────────────────────────────┤
│  quizzes_questions (empty - to populate)                        │
│  └── Questions with difficulty, concept_id, sub_concept         │
├─────────────────────────────────────────────────────────────────┤
│  chunks_hybrid (hybrid search - dense + sparse)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Difficulty Levels (Fresh/Soph/Junior)

Mapped to LibreTexts categories and course levels:

### Chemistry
| LibreTexts Category | Level | Course |
|---------------------|-------|--------|
| Introductory/GOB Chemistry | Freshman | 100-200 level |
| General Chemistry | Freshman/Soph | 100-200 level |
| Organic Chemistry | Soph/Junior | 200-300 level |
| Physical/Theoretical Chemistry | Junior | 300 level |
| Analytical Chemistry | Junior | 300 level |
| Inorganic Chemistry | Junior/Senior | 300-400 level |
| Biological Chemistry | Junior/Senior | 300-400 level |

### Physics
| LibreTexts Category | Level | Course |
|---------------------|-------|--------|
| Conceptual Physics | Freshman | 100 level |
| University Physics | Freshman/Soph | 100-200 level |
| Classical Mechanics | Soph/Junior | 200-300 level |
| Quantum Mechanics | Junior/Senior | 300-400 level |
| Thermodynamics | Junior | 300 level |

*(Similar mappings for Biology, Math, Engineering)*

---

## Curriculum Connection Workflow

### Step 1: Paper Comes In
```python
# From society_fetcher.py
paper = {
    "doi": "10.1021/acs.jacs.xxxxx",
    "title": "Novel Catalytic Mechanism...",
    "abstract": "We report a new SN2 reaction pathway..."
}
```

### Step 2: Query Qdrant for Related Curriculum
```bash
source /storage/RAG/.venv/bin/activate
python /storage/RAG/src/query.py "SN2 reaction mechanism nucleophilic substitution"
```

Returns matched chunks from LibreTexts with:
- `pdf_name`: e.g., `map_essential_organic_chemistry_bruice.pdf`
- `text`: Relevant curriculum content
- Score indicating relevance

### Step 3: Identify Difficulty Level
Based on which LibreTexts category the matches come from:
- Bruice Organic Chemistry → Soph/Junior (200-300 level)
- General Chemistry texts → Freshman (100-200 level)

### Step 4: Generate Curriculum Connection Section
```html
<div class="curriculum-connection">
    <h3>Curriculum Connection</h3>
    <div class="level-badge soph-junior">Sophomore/Junior (200-300 level)</div>

    <h4>Related Topics:</h4>
    <ul>
        <li><strong>Organic Chemistry:</strong> SN1 vs SN2 mechanisms, nucleophilicity</li>
        <li><strong>Physical Chemistry:</strong> Reaction kinetics, transition state theory</li>
    </ul>

    <h4>Prerequisite Concepts:</h4>
    <ul>
        <li>Lewis structures and electron pushing</li>
        <li>Stereochemistry basics</li>
    </ul>
</div>
```

---

## Quiz Generation Workflow

### Step 1: Use CURRICULUM_HOOKS
From `/storage/quizzes/app/embeddings.py`:
```python
CURRICULUM_HOOKS = [
    "equilibrium", "eigenvectors", "eigenvalues", "diffusion", "fourier",
    "kinetics", "thermodynamics", "maxwell", "schrodinger", "hardy-weinberg",
    "coordination", "isomerism", "ligand field", "crystal field",
    "stoichiometry", "limiting reagent", "yield", "molarity",
    "acid-base", "redox", "electrochemistry", "entropy", "enthalpy",
    "gibbs free energy", "activation energy", "rate law", "half-life",
    # skill hooks
    "dimensional analysis", "unit conversion", "significant figures",
    "graph interpretation", "data analysis", "hypothesis testing",
]
```

### Step 2: Match Paper to Concepts
```python
from quizzes.app.embeddings import find_related_concepts
concepts = find_related_concepts(paper["abstract"])
# Returns: ["kinetics", "activation energy", "rate law"]
```

### Step 3: Generate Quiz Questions
For each matched concept, generate questions at appropriate difficulty:

```python
# Question structure
question = {
    "question_id": "chem-kinetics-001",
    "concept_id": "kinetics",
    "sub_concept": "SN2_mechanism",
    "difficulty": "sophomore",  # fresh/soph/junior
    "type": "multiple_choice",
    "stem": "In an SN2 reaction, what happens to the rate when you double the nucleophile concentration?",
    "options": ["Doubles", "Quadruples", "Stays the same", "Halves"],
    "correct_answer": "Doubles",
    "explanation": "SN2 reactions are second-order: rate = k[substrate][nucleophile]. Doubling [Nu] doubles the rate."
}
```

### Step 4: Store in Qdrant
```python
from quizzes.app.qdrant_quiz import upsert_question_to_qdrant
upsert_question_to_qdrant(question)
```

---

## Key Files & Paths

| Component | Path | Description |
|-----------|------|-------------|
| RAG System | `/storage/RAG/` | Main RAG directory |
| LibreTexts | `/storage/ragstack/libretexts/` | 665 textbooks |
| Quiz System | `/storage/quizzes/` | Quiz API + database |
| Quiz DB | `/storage/quizzes/quiz.db` | SQLite database |
| Embeddings | `/storage/quizzes/app/embeddings.py` | Curriculum hooks |
| Qdrant Quiz | `/storage/quizzes/app/qdrant_quiz.py` | Quiz-Qdrant integration |

---

## Commands

### Query RAG for curriculum
```bash
source /storage/RAG/.venv/bin/activate
python /storage/RAG/src/query.py "YOUR TOPIC HERE"
```

### Interactive chat with RAG
```bash
python /storage/RAG/src/chat.py "explain SN2 mechanism"
```

### Check Qdrant collections
```bash
curl -s http://localhost:6333/collections | python3 -m json.tool
```

### Search quiz questions
```python
from quizzes.app.qdrant_quiz import search_questions
results = search_questions(concept_id="kinetics", difficulty="sophomore", k=5)
```

---

## Integration with Visual Stories & Deep Dives

### Visual Stories (Tacos)
- Single PDF → query Qdrant for curriculum matches
- Identify difficulty: Fresh/Soph/Junior
- Add curriculum connection section
- Add 3-5 quiz questions at matched difficulty

### Deep Dives (Big Enchilada)
- Collection of PDFs on topic → NotebookLM
- Broader curriculum mapping (multiple concepts)
- More comprehensive quiz bank (10-15 questions)
- Multiple difficulty levels covered

---

## Quiz Generation (IMPLEMENTED)

Quiz generation is now automated via `scripts/quiz_generator.py`.

### Commands
```bash
# generate quizzes for a specific topic
QUIZ_LLM_MODEL="qwen3:latest" python scripts/quiz_generator.py chemistry kinetics

# generate for entire discipline
python scripts/quiz_generator.py chemistry

# check question counts
python scripts/quiz_generator.py --count
```

### Current Status
- `quizzes_questions` collection: 5+ questions (growing)
- Uses Ollama LLM (qwen3 recommended) for question generation
- Queries Qdrant chunks_text for context
- Stores questions with difficulty level and curriculum tags

---

## Knowledge Graph Explorer

Interactive D3.js visualization at `/explore/`.

### Graph Data
```
data/graphs/
├── chemistry_graph.json    (22 topics, 91 books, 294 edges)
├── physics_graph.json      (20 topics, 31 books, 107 edges)
├── biology_graph.json      (20 topics, 68 books, 188 edges)
├── mathematics_graph.json  (20 topics, 72 books, 190 edges)
├── engineering_graph.json  (20 topics, 35 books, 75 edges)
├── ai_graph.json           (20 topics, 25 books, 56 edges)
└── agriculture_graph.json  (20 topics, 68 books, 195 edges)

TOTAL: 142 topics, 390 books, 1,105 edges
```

### Build/Rebuild
```bash
python scripts/knowledge_graph_builder.py              # all disciplines
python scripts/knowledge_graph_builder.py chemistry    # one discipline
python scripts/knowledge_graph_builder.py --stats      # show statistics
```

### Edge Types
| Type | Description |
|------|-------------|
| `covers` | Topic → Book (from Qdrant similarity) |
| `prerequisite` | Freshman → Sophomore → Junior topics |
| `related` | Topics with keyword overlap |

---

## LibreTexts Manifest

Located at: `/storage/ragstack/libretexts/MANIFEST.json`

```json
{
  "name": "Book Title",
  "url": "https://chem.libretexts.org/...",
  "category": {
    "name": "Organic Chemistry",
    "url": "..."
  },
  "domain": "chemistry",
  "files": {
    "pdf": "/path/to/book.pdf",
    "markdown_pdf": "/path/to/book.pdf.md"
  }
}
```

Total: 665 books across chemistry, physics, biology, math, engineering, statistics.
