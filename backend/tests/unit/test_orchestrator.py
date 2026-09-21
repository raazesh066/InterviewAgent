"""Unit tests for the Interview Orchestrator Agent's routing logic."""
import asyncio
from unittest.mock import AsyncMock

from app.agents.orchestrator import build_stage_plan, orchestrator_node
from app.agents.question_agents import _generate
from app.agents.schemas import GeneratedQuestion


def test_build_stage_plan_mixed():
    plan = build_stage_plan("Mixed")
    assert plan == ["technical", "system_design", "behavioral", "coding"]


def test_build_stage_plan_behavioral():
    assert build_stage_plan("Behavioral") == ["behavioral"]


def test_orchestrator_round_robins_through_stage_plan():
    state = {"interview_type": "Mixed", "question_count": 0}
    result = asyncio.run(orchestrator_node(dict(state)))
    assert result["next_agent"] == "technical"

    state["question_count"] = 2
    result = asyncio.run(orchestrator_node(dict(state)))
    assert result["next_agent"] == "behavioral"


def test_question_generation_retries_duplicate(monkeypatch):
    duplicate = GeneratedQuestion(
        question="How would you scale this service?",
        skill="System Design",
        difficulty="intermediate",
        expected_topics=["scalability"],
    )
    unique = GeneratedQuestion(
        question="How would you isolate tenants in this service?",
        skill="System Design",
        difficulty="intermediate",
        expected_topics=["security"],
    )
    client = AsyncMock()
    client.generate_structured.side_effect = [duplicate, unique]
    monkeypatch.setattr("app.agents.question_agents.get_azure_openai_client", lambda: client)
    state = {
        "history": [{"question": "How would you scale this service?"}],
        "current_difficulty": "intermediate",
        "skills": [{"name": "Azure", "level": "Advanced"}],
    }

    result = asyncio.run(_generate(state, "system_design", lambda _: ("system", "user")))

    assert result["generated_question"]["question"] == unique.question
    assert client.generate_structured.await_count == 2


def test_question_generation_falls_back_when_provider_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "app.agents.question_agents.get_azure_openai_client",
        lambda: (_ for _ in ()).throw(RuntimeError("Missing credentials")),
    )
    state = {
        "history": [],
        "current_difficulty": "intermediate",
        "skills": [{"name": "Python", "level": "Intermediate"}],
    }

    result = asyncio.run(_generate(state, "technical", lambda _: ("system", "user")))

    assert result["generated_question"]["agent_type"] == "technical"
    assert result["generated_question"]["skill"] == "Python"
    assert result["generated_question"]["question"]
