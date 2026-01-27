#!/usr/bin/env python3
"""
quiz_generator.py - generate quizzes from LibreTexts content via Qdrant

queries chunks_text for curriculum topics, uses Ollama LLM to generate
multiple-choice questions, and stores them in quizzes_questions collection.

usage:
    python quiz_generator.py                          # generate for all topics
    python quiz_generator.py chemistry kinetics       # specific discipline/topic
    python quiz_generator.py --list                   # show all topics
    python quiz_generator.py --count                  # show question counts
"""

import argparse
import json
import os
import random
import re
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models

# paths
SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
CURRICULUM_PATH = PROJECT_DIR / "data" / "curriculum.json"

# qdrant config
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
CHUNKS_COLLECTION = "chunks_text"
QUIZ_COLLECTION = "quizzes_questions"

# ollama config
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text:latest"
LLM_MODEL = os.environ.get("QUIZ_LLM_MODEL", "llama3.2:latest")
EMBED_DIM = 768

# generation limits
QUESTIONS_PER_TOPIC = 5
CHUNKS_PER_QUERY = 8


def load_curriculum() -> Dict:
    """load curriculum.json"""
    if not CURRICULUM_PATH.exists():
        print(f"[!] curriculum.json not found at {CURRICULUM_PATH}")
        sys.exit(1)

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


def query_qdrant_for_topic(client: QdrantClient, topic_name: str, keywords: List[str], k: int = CHUNKS_PER_QUERY) -> List[Dict]:
    """query qdrant chunks_text for topic content"""

    # combine topic name and keywords for better matching
    query_text = f"{topic_name} {' '.join(keywords)}"
    query_vec = get_embedding(query_text)

    try:
        # use query_points (newer API) instead of search
        results = client.query_points(
            collection_name=CHUNKS_COLLECTION,
            query=query_vec,
            limit=k,
            with_payload=True,
        )
        return [
            {
                "text": r.payload.get("text", ""),
                "pdf_name": r.payload.get("pdf_name", ""),
                "chunk_id": r.payload.get("chunk_id", 0),
                "score": r.score,
            }
            for r in results.points
        ]
    except Exception as e:
        print(f"[!] qdrant search error: {e}")
        return []


def generate_questions_with_llm(
    topic_name: str,
    topic_slug: str,
    keywords: List[str],
    difficulty: str,
    discipline: str,
    subfield: str,
    context_chunks: List[Dict],
    n_questions: int = QUESTIONS_PER_TOPIC
) -> List[Dict]:
    """generate quiz questions using Ollama LLM"""

    # combine context from chunks
    context_text = "\n\n---\n\n".join([
        f"Source: {c['pdf_name']}\n{c['text'][:1500]}"
        for c in context_chunks[:5]
    ])

    difficulty_level = {
        "freshman": "100-level introductory",
        "sophomore": "200-level intermediate",
        "junior": "300-level advanced",
    }.get(difficulty, "undergraduate")

    prompt = f"""You are creating multiple-choice quiz questions for undergraduate students studying {discipline}.

Topic: {topic_name}
Difficulty Level: {difficulty_level}
Subfield: {subfield}
Key concepts: {', '.join(keywords)}

Use this educational content as reference:
{context_text}

Generate exactly {n_questions} multiple-choice questions. Each question should:
1. Test understanding, not memorization
2. Be appropriate for {difficulty_level} students
3. Have 4 options (A, B, C, D) with exactly one correct answer
4. Include a brief explanation of why the correct answer is right

Format your response as JSON array:
[
  {{
    "stem": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation of the correct answer"
  }}
]

Return ONLY the JSON array, no other text."""

    # call Ollama
    payload = json.dumps({
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 4096,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            response_text = data.get("response", "")
    except Exception as e:
        print(f"[!] LLM generation error: {e}")
        return []

    # parse JSON from response
    questions = parse_llm_questions(response_text, topic_name, topic_slug, difficulty, discipline, subfield)
    return questions


def parse_llm_questions(
    response_text: str,
    topic_name: str,
    topic_slug: str,
    difficulty: str,
    discipline: str,
    subfield: str
) -> List[Dict]:
    """parse LLM response into question dicts"""

    # strip thinking tags (qwen3 uses <think>...</think>)
    clean_text = re.sub(r'<think>[\s\S]*?</think>', '', response_text)

    # try to extract JSON array from response
    json_match = re.search(r'\[[\s\S]*\]', clean_text)
    if not json_match:
        print(f"[!] could not find JSON in LLM response")
        return []

    json_str = json_match.group()

    # fix common JSON issues: trailing commas before ] or }
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = re.sub(r',\s*}', '}', json_str)

    try:
        raw_questions = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[!] JSON parse error: {e}")
        return []

    questions = []
    for i, q in enumerate(raw_questions):
        if not all(k in q for k in ["stem", "options", "correct_answer"]):
            continue

        # generate unique question_id
        question_id = f"{discipline[:4]}-{topic_slug}-{i+1:03d}-{random.randint(1000, 9999)}"

        questions.append({
            "question_id": question_id,
            "concept_id": topic_slug,
            "sub_concept": subfield.lower().replace(" ", "_"),
            "difficulty": difficulty,
            "type": "multiple_choice",
            "stem": q["stem"],
            "options": q["options"][:4],  # ensure max 4 options
            "correct_answer": q["correct_answer"],
            "explanation": q.get("explanation", ""),
            "discipline": discipline,
            "topic_name": topic_name,
        })

    return questions


def upsert_questions_to_qdrant(client: QdrantClient, questions: List[Dict]) -> int:
    """upsert questions to quizzes_questions collection"""

    # ensure collection exists
    try:
        collections = client.get_collections().collections
        existing = {c.name for c in collections}
        if QUIZ_COLLECTION not in existing:
            client.create_collection(
                collection_name=QUIZ_COLLECTION,
                vectors_config=models.VectorParams(size=EMBED_DIM, distance=models.Distance.COSINE),
            )
            print(f"[+] created collection: {QUIZ_COLLECTION}")
    except Exception as e:
        print(f"[!] collection check error: {e}")
        return 0

    # upsert questions
    points = []
    for q in questions:
        # embed question stem + options for vector search
        embed_text = q["stem"] + " " + " ".join(q.get("options", []))
        vector = get_embedding(embed_text)

        points.append(models.PointStruct(
            id=hash(q["question_id"]) & 0x7FFFFFFFFFFFFFFF,  # positive int64
            vector=vector,
            payload=q,
        ))

    try:
        client.upsert(collection_name=QUIZ_COLLECTION, points=points)
        return len(points)
    except Exception as e:
        print(f"[!] upsert error: {e}")
        return 0


def get_all_topics(curriculum: Dict) -> List[Tuple[str, str, str, Dict]]:
    """get all topics from curriculum as (discipline, subfield, topic_name, topic_data)"""

    topics = []
    for discipline, disc_data in curriculum.items():
        if discipline.startswith("_"):  # skip _meta
            continue
        for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
            difficulty = subfield_data.get("difficulty", "sophomore")
            for topic in subfield_data.get("topics", []):
                topics.append((discipline, subfield_name, difficulty, topic))

    return topics


def list_topics(curriculum: Dict):
    """print all topics"""

    print("\n=== CURRICULUM TOPICS ===\n")
    for discipline, disc_data in curriculum.items():
        if discipline.startswith("_"):
            continue
        print(f"\n{discipline.upper()}")
        for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
            level = subfield_data.get("level", "")
            difficulty = subfield_data.get("difficulty", "")
            print(f"  {subfield_name} ({level}, {difficulty})")
            for topic in subfield_data.get("topics", []):
                print(f"    - {topic['name']} [{topic['slug']}]")


def count_questions(client: QdrantClient):
    """print question counts by discipline/topic"""

    try:
        info = client.get_collection(QUIZ_COLLECTION)
        total = info.points_count
        print(f"\n=== QUIZ QUESTIONS: {total} total ===\n")

        if total == 0:
            print("No questions yet. Run quiz_generator.py to populate.")
            return

        # get sample to show breakdown
        results = client.scroll(
            collection_name=QUIZ_COLLECTION,
            limit=1000,
            with_payload=True,
        )

        by_discipline = {}
        by_difficulty = {}
        for point in results[0]:
            disc = point.payload.get("discipline", "unknown")
            diff = point.payload.get("difficulty", "unknown")
            by_discipline[disc] = by_discipline.get(disc, 0) + 1
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1

        print("By discipline:")
        for d, c in sorted(by_discipline.items()):
            print(f"  {d}: {c}")

        print("\nBy difficulty:")
        for d, c in sorted(by_difficulty.items()):
            print(f"  {d}: {c}")

    except Exception as e:
        print(f"[!] error counting questions: {e}")


def generate_for_topic(
    client: QdrantClient,
    discipline: str,
    subfield: str,
    difficulty: str,
    topic: Dict,
    verbose: bool = True
) -> int:
    """generate questions for a single topic"""

    topic_name = topic["name"]
    topic_slug = topic["slug"]
    keywords = topic.get("keywords", [])

    if verbose:
        print(f"  generating: {topic_name}...")

    # query qdrant for context
    chunks = query_qdrant_for_topic(client, topic_name, keywords)
    if not chunks:
        if verbose:
            print(f"    [!] no context found")
        return 0

    # generate questions
    questions = generate_questions_with_llm(
        topic_name=topic_name,
        topic_slug=topic_slug,
        keywords=keywords,
        difficulty=difficulty,
        discipline=discipline,
        subfield=subfield,
        context_chunks=chunks,
    )

    if not questions:
        if verbose:
            print(f"    [!] no questions generated")
        return 0

    # upsert to qdrant
    count = upsert_questions_to_qdrant(client, questions)
    if verbose:
        print(f"    [+] {count} questions")

    return count


def main():
    parser = argparse.ArgumentParser(description="Generate quizzes from LibreTexts content")
    parser.add_argument("discipline", nargs="?", help="Discipline (e.g., chemistry)")
    parser.add_argument("topic", nargs="?", help="Topic slug (e.g., kinetics)")
    parser.add_argument("--list", action="store_true", help="List all topics")
    parser.add_argument("--count", action="store_true", help="Show question counts")
    parser.add_argument("--limit", type=int, default=0, help="Limit topics to generate")
    args = parser.parse_args()

    curriculum = load_curriculum()
    client = get_qdrant_client()

    if args.list:
        list_topics(curriculum)
        return

    if args.count:
        count_questions(client)
        return

    # generate for specific discipline/topic
    if args.discipline:
        if args.discipline not in curriculum:
            print(f"[!] unknown discipline: {args.discipline}")
            print(f"    available: {', '.join(k for k in curriculum.keys() if not k.startswith('_'))}")
            return

        disc_data = curriculum[args.discipline]
        total = 0

        print(f"\n[{args.discipline.upper()}]")

        for subfield_name, subfield_data in disc_data.get("subfields", {}).items():
            difficulty = subfield_data.get("difficulty", "sophomore")

            for topic in subfield_data.get("topics", []):
                # filter by specific topic if provided
                if args.topic and topic["slug"] != args.topic:
                    continue

                count = generate_for_topic(
                    client, args.discipline, subfield_name, difficulty, topic
                )
                total += count

        print(f"\n  total: {total} questions")
        return

    # generate for all disciplines
    print("\n=== GENERATING QUIZ QUESTIONS ===")
    topics = get_all_topics(curriculum)
    total = 0

    if args.limit:
        topics = topics[:args.limit]

    for discipline, subfield, difficulty, topic in topics:
        count = generate_for_topic(client, discipline, subfield, difficulty, topic)
        total += count

    print(f"\n=== COMPLETE: {total} questions generated ===")


if __name__ == "__main__":
    main()
