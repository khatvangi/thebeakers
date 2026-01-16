#!/usr/bin/env python3
"""
rag_integration.py - connect thebeakers to RAG system
provides: fact-checking, citation lookup, content generation support
"""

import os
import sys
sys.path.insert(0, "/storage")

from typing import List, Dict, Any, Optional
from course_glossary import (
    SUBJECTS, CONCEPT_HOOKS, SKILL_HOOKS,
    search_course_content, get_concept_definition,
    find_topics_by_hook
)

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")


def get_citations_for_claim(claim: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    find RAG sources that support a claim
    returns: list of {text, source, page, score}
    """
    return search_course_content(claim, limit=limit)


def fact_check(statement: str, threshold: float = 0.6) -> Dict[str, Any]:
    """
    check if a statement is supported by indexed content
    returns: {supported: bool, confidence: float, sources: [...]}
    """
    results = search_course_content(statement, limit=3)
    if not results:
        return {"supported": False, "confidence": 0.0, "sources": []}

    top_score = results[0]["score"]
    return {
        "supported": top_score >= threshold,
        "confidence": top_score,
        "sources": results,
    }


def generate_curriculum_bridge(topic: str) -> Dict[str, Any]:
    """
    generate curriculum bridge content for an article topic
    finds: related concepts, prerequisites, skill hooks
    """
    # find matching curriculum hooks
    matching_hooks = [h for h in CONCEPT_HOOKS if h.lower() in topic.lower()]

    # find related topics across subjects
    related_topics = []
    for hook in matching_hooks:
        related_topics.extend(find_topics_by_hook(hook))

    # get definition from RAG
    definition = get_concept_definition(topic)

    return {
        "topic": topic,
        "curriculum_hooks": matching_hooks,
        "skill_hooks": [s for s in SKILL_HOOKS if any(h.lower() in s.lower() for h in matching_hooks)],
        "related_topics": related_topics[:5],
        "definition": definition,
    }


def get_article_context(article_topic: str, article_type: str = "indepth") -> Dict[str, Any]:
    """
    get full context for writing a beakers article
    """
    # search RAG for relevant content
    rag_results = search_course_content(article_topic, limit=5)

    # get curriculum bridge
    bridge = generate_curriculum_bridge(article_topic)

    # determine difficulty based on topic complexity
    difficulty = "intermediate"
    advanced_keywords = ["quantum", "relativistic", "tensor", "manifold", "topology"]
    basic_keywords = ["introduction", "basic", "fundamental", "simple"]
    if any(k in article_topic.lower() for k in advanced_keywords):
        difficulty = "advanced"
    elif any(k in article_topic.lower() for k in basic_keywords):
        difficulty = "beginner"

    return {
        "topic": article_topic,
        "type": article_type,
        "difficulty": difficulty,
        "rag_sources": rag_results,
        "curriculum_bridge": bridge,
        "suggested_hooks": bridge["curriculum_hooks"][:3],
        "suggested_skills": bridge["skill_hooks"][:2],
    }


# scoring helpers for content routing
def score_for_beakers(
    significance: int,
    evidence: int,
    teachability: int,
    media: int,
    hype: int
) -> Dict[str, Any]:
    """
    apply beakers scoring rubric
    returns routing decision and scores
    """
    scores = {"S": significance, "E": evidence, "T": teachability, "M": media, "H": hype}

    # routing rules from CONTENT_SYSTEM.md
    if evidence >= 4 and teachability >= 4 and (significance >= 4 or media >= 4) and hype <= 2:
        route = "indepth"
    elif evidence >= 3 and teachability >= 3 and (significance >= 3 or media >= 3) and hype <= 3:
        route = "digest"
    elif teachability >= 2 and (significance >= 3 or media >= 3):
        route = "blurb"
        if evidence <= 2:
            route = "blurb_frontier"
    else:
        route = "reject"

    return {
        "scores": scores,
        "route": route,
        "total": sum(scores.values()) - hype,  # hype is penalty
    }


if __name__ == "__main__":
    # test
    print("=== Testing RAG Integration ===\n")

    # test fact check
    print("Fact check: 'eigenvalues determine matrix diagonalizability'")
    result = fact_check("eigenvalues determine matrix diagonalizability")
    print(f"  Supported: {result['supported']}, Confidence: {result['confidence']:.2f}")

    # test curriculum bridge
    print("\nCurriculum bridge for 'ligand field theory':")
    bridge = generate_curriculum_bridge("ligand field theory")
    print(f"  Hooks: {bridge['curriculum_hooks']}")
    print(f"  Related: {[t['name'] for t in bridge['related_topics']]}")

    # test article context
    print("\nArticle context for 'crystal field splitting':")
    ctx = get_article_context("crystal field splitting")
    print(f"  Difficulty: {ctx['difficulty']}")
    print(f"  Suggested hooks: {ctx['suggested_hooks']}")
