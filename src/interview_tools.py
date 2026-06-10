"""Interview question bank tools for the technical interviewer agent."""

from __future__ import annotations

import random
from pathlib import Path
from threading import Lock
from typing import Any

import yaml
from langchain_core.tools import tool
from langgraph.config import get_config

QUESTIONS_DIR = Path(__file__).resolve().parent.parent / "config" / "questions"

# Per-session tracking of used question IDs (thread_id -> set of question ids)
_used_questions: dict[str, set[str]] = {}
_lock = Lock()

TOPIC_ALIASES = {
    "fe": "frontend",
    "frontend": "frontend",
    "react": "frontend",
    "javascript": "frontend",
    "js": "frontend",
    "be": "backend",
    "backend": "backend",
    "api": "backend",
    "database": "backend",
    "db": "backend",
    "sd": "system_design",
    "system_design": "system_design",
    "system design": "system_design",
    "systemdesign": "system_design",
    "design": "system_design",
}

DIFFICULTY_ALIASES = {
    "junior": "junior",
    "jr": "junior",
    "entry": "junior",
    "mid": "mid",
    "middle": "mid",
    "intermediate": "mid",
    "senior": "senior",
    "sr": "senior",
    "lead": "senior",
}


def _normalize_topic(topic: str) -> str:
    key = topic.strip().lower()
    if key not in TOPIC_ALIASES:
        raise ValueError(
            f"Unknown topic '{topic}'. Valid topics: frontend, backend, system_design"
        )
    return TOPIC_ALIASES[key]


def _normalize_difficulty(difficulty: str) -> str:
    key = difficulty.strip().lower()
    if key not in DIFFICULTY_ALIASES:
        raise ValueError(
            f"Unknown difficulty '{difficulty}'. Valid levels: junior, mid, senior"
        )
    return DIFFICULTY_ALIASES[key]


def _get_thread_id() -> str:
    config = get_config()
    return config["configurable"].get("thread_id", "default")


def _load_all_questions() -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for path in sorted(QUESTIONS_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        questions.extend(data.get("questions", []))
    return questions


def _format_question(q: dict[str, Any]) -> str:
    lines = [
        f"ID: {q['id']}",
        f"Topic: {q['topic']}",
        f"Difficulty: {q['difficulty']}",
        f"Question: {q['question']}",
    ]
    if q.get("follow_ups"):
        lines.append("Follow-ups (use if candidate answers well):")
        for fu in q["follow_ups"]:
            lines.append(f"  - {fu}")
    if q.get("evaluation_criteria"):
        lines.append("Evaluation criteria (internal — do not reveal to candidate):")
        for c in q["evaluation_criteria"]:
            lines.append(f"  - {c}")
    if q.get("sample_good_points"):
        lines.append("Sample good points (internal):")
        for p in q["sample_good_points"]:
            lines.append(f"  - {p}")
    return "\n".join(lines)


@tool
def list_topics() -> str:
    """List available interview topics and difficulty levels in the question bank."""
    questions = _load_all_questions()
    by_topic: dict[str, set[str]] = {}
    for q in questions:
        topic = q["topic"]
        by_topic.setdefault(topic, set()).add(q["difficulty"])

    lines = ["Available interview topics:\n"]
    labels = {
        "frontend": "Frontend (React, JavaScript, CSS, performance)",
        "backend": "Backend (API, database, caching)",
        "system_design": "System Design (scalability, architecture)",
    }
    for topic in sorted(by_topic):
        levels = ", ".join(sorted(by_topic[topic]))
        label = labels.get(topic, topic)
        count = sum(1 for q in questions if q["topic"] == topic)
        lines.append(f"- **{topic}** — {label}")
        lines.append(f"  Levels: {levels} ({count} questions)")
    return "\n".join(lines)


@tool
def get_question(topic: str, difficulty: str) -> str:
    """Fetch the next interview question from the bank for a topic and difficulty level.

    Args:
        topic: Interview topic — frontend, backend, or system_design (aliases: react, api, design).
        difficulty: Level — junior, mid, or senior.
    """
    norm_topic = _normalize_topic(topic)
    norm_difficulty = _normalize_difficulty(difficulty)
    thread_id = _get_thread_id()

    all_questions = _load_all_questions()
    pool = [
        q
        for q in all_questions
        if q["topic"] == norm_topic and q["difficulty"] == norm_difficulty
    ]

    if not pool:
        return (
            f"No questions found for topic='{norm_topic}' difficulty='{norm_difficulty}'. "
            "Use list_topics to see available options or try a different level."
        )

    with _lock:
        used = _used_questions.setdefault(thread_id, set())
        available = [q for q in pool if q["id"] not in used]

    if not available:
        with _lock:
            _used_questions[thread_id] = set()
            available = pool

    chosen = random.choice(available)

    with _lock:
        _used_questions[thread_id].add(chosen["id"])

    return _format_question(chosen)
