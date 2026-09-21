"""Question-generating agent nodes (Technical, Behavioral, System Design, Coding).

Each node reads `InterviewGraphState`, calls Azure OpenAI for a structured
`GeneratedQuestion`, and writes the result back into `state['generated_question']`.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict

from app.agents.prompts.templates import (
    build_behavioral_question_prompt,
    build_coding_question_prompt,
    build_system_design_question_prompt,
    build_technical_question_prompt,
)
from app.agents.schemas import GeneratedQuestion
from app.core.logging import get_logger
from app.infrastructure.azure_openai.client import get_azure_openai_client

logger = get_logger(__name__)


def _normalize_question(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _is_duplicate(question: str, history: list[Dict[str, Any]]) -> bool:
    normalized = _normalize_question(question)
    for entry in history:
        previous = _normalize_question(str(entry.get("question", "")))
        if previous and (normalized == previous or SequenceMatcher(None, normalized, previous).ratio() >= 0.88):
            return True
    return False


def _fallback_question(state: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
    skill = next((item.get("name") for item in state.get("skills", []) if item.get("name")), "your primary skill")
    difficulty = state.get("current_difficulty", "intermediate")
    variants = {
        "technical": [
            (f"Describe a production failure involving {skill} that you would investigate. What evidence would you collect first, and how would you prevent it recurring?", ["diagnosis", "observability", "prevention"]),
            (f"How would you review a {skill} solution for reliability, security, and maintainability before approving it for production?", ["reliability", "security", "maintainability"]),
            (f"Explain a difficult tradeoff you might face when scaling a {skill} workload, including the metrics that would guide your decision.", ["scalability", "tradeoffs", "metrics"]),
        ],
        "behavioral": [
            ("Tell me about a time you changed a technical decision after receiving new evidence. What did you do and what was the result?", ["adaptability", "ownership", "communication"]),
            ("Tell me about a time you had to align people with conflicting priorities. How did you reach a decision?", ["leadership", "conflict resolution", "collaboration"]),
            ("Describe a project where your first approach did not work. How did you recover and what did you learn?", ["resilience", "ownership", "learning"]),
        ],
        "system_design": [
            (f"Design a multi-tenant platform centered on {skill}. How would you isolate tenants and handle regional failures?", ["scalability", "security", "reliability"]),
            ("Design a service that ingests, processes, and searches millions of audit events each day.", ["scalability", "availability", "cost optimization"]),
            ("Design a feature-flag service used by globally distributed applications with strict availability requirements.", ["availability", "reliability", "security"]),
        ],
        "coding": [
            ("Given a stream of events with timestamps and identifiers, return the identifiers seen more than once within a rolling time window.", ["hash maps", "sliding window", "edge cases"]),
            ("Given a dependency graph, return a valid execution order or report that no valid order exists.", ["graphs", "topological sort", "cycle detection"]),
            ("Implement an in-memory least-recently-used cache with constant-time get and put operations.", ["hash maps", "linked lists", "complexity"]),
        ],
    }
    history = state.get("history", [])
    for text, topics in variants[agent_type]:
        if not _is_duplicate(text, history):
            return {"question": text, "skill": skill if agent_type == "technical" else agent_type.replace("_", " ").title(), "difficulty": difficulty, "expected_topics": topics}
    sequence = int(state.get("question_count", len(history))) + 1
    return {
        "question": f"Question {sequence}: Walk through a distinct {agent_type.replace('_', ' ')} challenge from your experience, the constraints you faced, and the tradeoffs you made.",
        "skill": skill,
        "difficulty": difficulty,
        "expected_topics": ["constraints", "tradeoffs", "outcomes"],
    }


async def _generate(state: Dict[str, Any], agent_type: str, prompt_builder) -> Dict[str, Any]:
    history = list(state.get("history", []))
    generated: Dict[str, Any] | None = None
    try:
        client = get_azure_openai_client()
        for attempt in range(3):
            prompt_state = {**state, "history": history}
            system_prompt, user_prompt = prompt_builder(prompt_state)
            question: GeneratedQuestion = await client.generate_structured(system_prompt, user_prompt, GeneratedQuestion)
            generated = question.model_dump()
            if not _is_duplicate(question.question, history):
                break
            logger.warning("duplicate_question_rejected", agent_type=agent_type, attempt=attempt + 1)
            history.append({"question": question.question, "agent_type": agent_type, "difficulty": question.difficulty})
        else:
            generated = _fallback_question(state, agent_type)
    except Exception as exc:
        logger.warning("question_provider_unavailable", agent_type=agent_type, error=str(exc))
        generated = _fallback_question(state, agent_type)

    logger.info("question_generated", agent_type=agent_type, skill=generated.get("skill"), difficulty=generated.get("difficulty"))
    state["generated_question"] = {**generated, "agent_type": agent_type}
    return state


async def technical_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return await _generate(state, "technical", build_technical_question_prompt)


async def behavioral_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return await _generate(state, "behavioral", build_behavioral_question_prompt)


async def system_design_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return await _generate(state, "system_design", build_system_design_question_prompt)


async def coding_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return await _generate(state, "coding", build_coding_question_prompt)
