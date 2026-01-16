#!/usr/bin/env python3
"""
knowledge_graph_builder.py - build knowledge graphs from curriculum + Qdrant

creates interactive knowledge graphs showing:
- topics (from curriculum.json)
- books (from LibreTexts via Qdrant)
- edges: prerequisite, related, covers

usage:
    python knowledge_graph_builder.py                 # build all disciplines
    python knowledge_graph_builder.py chemistry       # build one discipline
    python knowledge_graph_builder.py --stats         # show graph statistics
"""

import argparse
import json
import os
import re
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from qdrant_client import QdrantClient

# paths
SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
CURRICULUM_PATH = PROJECT_DIR / "data" / "curriculum.json"
GRAPHS_DIR = PROJECT_DIR / "data" / "graphs"

# qdrant config
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
CHUNKS_COLLECTION = "chunks_text"

# ollama config
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text:latest"
EMBED_DIM = 768

# graph config
MIN_BOOK_SCORE = 0.55  # minimum similarity to link topic-book
MIN_TOPIC_SCORE = 0.65  # minimum similarity for topic-topic related edges
TOP_K_BOOKS = 15  # max books per topic


def load_curriculum() -> Dict:
    """load curriculum.json"""
    with open(CURRICULUM_PATH) as f:
        return json.load(f)


def get_qdrant_client() -> QdrantClient:
    """get qdrant client"""
    return QdrantClient(url=QDRANT_URL)


def get_embedding(text: str) -> List[float]:
    """get embedding for text using Ollama"""
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding", [0.0] * EMBED_DIM)
    except Exception as e:
        print(f"[!] embedding error: {e}")
        return [0.0] * EMBED_DIM


def normalize_book_name(pdf_name: str) -> Tuple[str, str]:
    """normalize PDF name to readable book title and ID"""
    # remove .pdf extension
    name = pdf_name.replace(".pdf", "").replace(".PDF", "")

    # common patterns to clean
    name = re.sub(r'_+', ' ', name)
    name = re.sub(r'-+', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    # create ID from cleaned name
    book_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:50]

    # title case for display
    title = name.title()

    # truncate very long titles
    if len(title) > 60:
        title = title[:57] + "..."

    return book_id, title


def query_books_for_topic(client: QdrantClient, topic_name: str, keywords: List[str]) -> List[Dict]:
    """find books related to a topic via Qdrant"""

    # build query from topic + keywords
    query_text = f"{topic_name} {' '.join(keywords)}"
    query_vec = get_embedding(query_text)

    try:
        results = client.query_points(
            collection_name=CHUNKS_COLLECTION,
            query=query_vec,
            limit=50,  # get more, then dedupe by book
            with_payload=True,
        )

        # aggregate by book
        books = {}
        for r in results.points:
            if r.score < MIN_BOOK_SCORE:
                continue

            pdf_name = r.payload.get("pdf_name", "")
            if not pdf_name:
                continue

            book_id, book_title = normalize_book_name(pdf_name)

            if book_id not in books:
                books[book_id] = {
                    "id": f"book-{book_id}",
                    "title": book_title,
                    "pdf_name": pdf_name,
                    "score": r.score,
                    "chunks": 1,
                }
            else:
                # update with better score and count chunks
                books[book_id]["score"] = max(books[book_id]["score"], r.score)
                books[book_id]["chunks"] += 1

        # sort by score and return top K
        sorted_books = sorted(books.values(), key=lambda x: (-x["score"], -x["chunks"]))
        return sorted_books[:TOP_K_BOOKS]

    except Exception as e:
        print(f"[!] qdrant error: {e}")
        return []


def compute_topic_similarity(topic1_keywords: List[str], topic2_keywords: List[str]) -> float:
    """compute keyword overlap similarity between topics"""
    set1 = set(k.lower() for k in topic1_keywords)
    set2 = set(k.lower() for k in topic2_keywords)

    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def get_difficulty_order(difficulty: str) -> int:
    """get numeric order for difficulty"""
    return {"freshman": 1, "sophomore": 2, "junior": 3}.get(difficulty, 2)


def build_discipline_graph(discipline: str, curriculum: Dict, client: QdrantClient, verbose: bool = True) -> Dict:
    """build knowledge graph for one discipline"""

    if discipline not in curriculum:
        return {"nodes": [], "edges": []}

    disc_data = curriculum[discipline]
    disc_meta = {
        "name": disc_data.get("name", discipline.title()),
        "icon": disc_data.get("icon", "📚"),
        "color": disc_data.get("color", "#3b82f6"),
    }

    nodes = []
    edges = []
    all_books = {}  # dedupe books across topics
    topic_data = []  # for computing topic-topic edges

    if verbose:
        print(f"\n[{discipline.upper()}]")

    # phase 1: create topic nodes and find books
    for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
        difficulty = subfield_data.get("difficulty", "sophomore")
        level = subfield_data.get("level", "200-300")

        for topic in subfield_data.get("topics", []):
            topic_name = topic["name"]
            topic_slug = topic["slug"]
            keywords = topic.get("keywords", [])

            topic_id = f"topic-{topic_slug}"

            if verbose:
                print(f"  {topic_name}...", end=" ", flush=True)

            # create topic node
            nodes.append({
                "id": topic_id,
                "type": "topic",
                "label": topic_name,
                "subfield": subfield_name,
                "difficulty": difficulty,
                "level": level,
                "keywords": keywords,
            })

            # store for later edge computation
            topic_data.append({
                "id": topic_id,
                "name": topic_name,
                "subfield": subfield_name,
                "difficulty": difficulty,
                "keywords": keywords,
            })

            # find related books
            books = query_books_for_topic(client, topic_name, keywords)

            if verbose:
                print(f"{len(books)} books")

            for book in books:
                book_id = book["id"]

                # add book node if not seen
                if book_id not in all_books:
                    all_books[book_id] = {
                        "id": book_id,
                        "type": "book",
                        "label": book["title"],
                        "pdf_name": book["pdf_name"],
                        "topics": [],
                    }

                all_books[book_id]["topics"].append(topic_id)

                # create topic-book edge
                edges.append({
                    "source": topic_id,
                    "target": book_id,
                    "type": "covers",
                    "weight": round(book["score"], 3),
                })

    # add book nodes
    nodes.extend(all_books.values())

    # phase 2: compute topic-topic edges
    if verbose:
        print(f"  computing topic relationships...")

    # group topics by difficulty for prerequisite chains
    by_difficulty = {"freshman": [], "sophomore": [], "junior": []}
    for t in topic_data:
        d = t["difficulty"]
        if d in by_difficulty:
            by_difficulty[d].append(t)

    # prerequisite edges: connect difficulty levels (not all pairs, just representative)
    # freshman → sophomore (pick 2-3 connections per sophomore topic)
    for soph_topic in by_difficulty["sophomore"]:
        # connect to freshman topics with keyword overlap, or first few
        connections = 0
        for fresh_topic in by_difficulty["freshman"]:
            sim = compute_topic_similarity(fresh_topic["keywords"], soph_topic["keywords"])
            if sim > 0 or connections < 2:
                edges.append({
                    "source": fresh_topic["id"],
                    "target": soph_topic["id"],
                    "type": "prerequisite",
                    "weight": round(0.7 + sim * 0.3, 3),
                })
                connections += 1
                if connections >= 3:
                    break

    # sophomore → junior
    for junior_topic in by_difficulty["junior"]:
        connections = 0
        for soph_topic in by_difficulty["sophomore"]:
            sim = compute_topic_similarity(soph_topic["keywords"], junior_topic["keywords"])
            if sim > 0 or connections < 2:
                edges.append({
                    "source": soph_topic["id"],
                    "target": junior_topic["id"],
                    "type": "prerequisite",
                    "weight": round(0.7 + sim * 0.3, 3),
                })
                connections += 1
                if connections >= 3:
                    break

    # related edges: keyword overlap within same difficulty level
    for i, t1 in enumerate(topic_data):
        for t2 in topic_data[i+1:]:
            if t1["subfield"] == t2["subfield"]:
                continue  # skip same subfield

            sim = compute_topic_similarity(t1["keywords"], t2["keywords"])
            if sim > 0:
                edges.append({
                    "source": t1["id"],
                    "target": t2["id"],
                    "type": "related",
                    "weight": round(0.5 + sim * 0.5, 3),
                })

    # build final graph
    graph = {
        "discipline": discipline,
        "meta": disc_meta,
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "topics": len([n for n in nodes if n["type"] == "topic"]),
            "books": len([n for n in nodes if n["type"] == "book"]),
            "edges": len(edges),
            "prerequisite_edges": len([e for e in edges if e["type"] == "prerequisite"]),
            "related_edges": len([e for e in edges if e["type"] == "related"]),
            "covers_edges": len([e for e in edges if e["type"] == "covers"]),
        }
    }

    if verbose:
        print(f"  → {graph['stats']['topics']} topics, {graph['stats']['books']} books, {graph['stats']['edges']} edges")

    return graph


def save_graph(graph: Dict, discipline: str):
    """save graph to JSON file"""
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GRAPHS_DIR / f"{discipline}_graph.json"

    with open(output_path, "w") as f:
        json.dump(graph, f, indent=2)

    print(f"  saved: {output_path}")


def show_stats():
    """show statistics for all graphs"""
    print("\n=== KNOWLEDGE GRAPH STATISTICS ===\n")

    if not GRAPHS_DIR.exists():
        print("No graphs built yet. Run: python knowledge_graph_builder.py")
        return

    total_topics = 0
    total_books = 0
    total_edges = 0

    for graph_file in sorted(GRAPHS_DIR.glob("*_graph.json")):
        with open(graph_file) as f:
            graph = json.load(f)

        discipline = graph["discipline"]
        stats = graph["stats"]

        print(f"{discipline.upper()}")
        print(f"  Topics: {stats['topics']}")
        print(f"  Books: {stats['books']}")
        print(f"  Edges: {stats['edges']}")
        print(f"    prerequisite: {stats['prerequisite_edges']}")
        print(f"    related: {stats['related_edges']}")
        print(f"    covers: {stats['covers_edges']}")
        print()

        total_topics += stats['topics']
        total_books += stats['books']
        total_edges += stats['edges']

    print(f"TOTAL: {total_topics} topics, {total_books} books, {total_edges} edges")


def main():
    parser = argparse.ArgumentParser(description="Build knowledge graphs from curriculum + Qdrant")
    parser.add_argument("discipline", nargs="?", help="Discipline to build (or all)")
    parser.add_argument("--stats", action="store_true", help="Show graph statistics")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    curriculum = load_curriculum()
    client = get_qdrant_client()

    # get list of disciplines
    disciplines = [k for k in curriculum.keys() if not k.startswith("_")]

    if args.discipline:
        if args.discipline not in disciplines:
            print(f"[!] unknown discipline: {args.discipline}")
            print(f"    available: {', '.join(disciplines)}")
            return
        disciplines = [args.discipline]

    print("\n=== BUILDING KNOWLEDGE GRAPHS ===")

    for discipline in disciplines:
        graph = build_discipline_graph(discipline, curriculum, client)
        save_graph(graph, discipline)

    print("\nDone. Run with --stats to see statistics.")


if __name__ == "__main__":
    main()
