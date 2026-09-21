"""Interview Orchestrator Agent — decides which specialized agent should ask the next
question, based on the interview_type, the stage plan, and how many questions of each
type have already been asked. This is the LangGraph entry / router node.
"""
from __future__ import annotations

from typing import Any, Dict

from app.core.logging import get_logger

logger = get_logger(__name__)

# Maps a high-level interview_type to the ordered sequence of specialized agents to cycle through.
STAGE_AGENT_MAP = {
    "Technical": ["technical", "coding"],
    "Behavioral": ["behavioral"],
    "System Design": ["system_design"],
    "Leadership": ["behavioral"],
    "Mixed": ["technical", "system_design", "behavioral", "coding"],
}


def build_stage_plan(interview_type: str) -> list[str]:
    return STAGE_AGENT_MAP.get(interview_type, ["technical"])


async def orchestrator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Route to the next specialized agent using round-robin over the stage plan,
    weighted slightly so 'technical' gets asked more often for technical-heavy types.
    """
    stage_plan: list[str] = state.get("stage_plan") or build_stage_plan(state.get("interview_type", "Technical"))
    state["stage_plan"] = stage_plan

    question_count = state.get("question_count", 0)
    idx = question_count % len(stage_plan)
    next_agent = stage_plan[idx]
    state["next_agent"] = next_agent
    logger.info(
        "orchestrator_routed",
        interview_id=state.get("interview_id"),
        question_count=question_count,
        next_agent=next_agent,
    )
    return state


def route_after_orchestrator(state: Dict[str, Any]) -> str:
    return state.get("next_agent", "technical")
