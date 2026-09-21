"""Evaluation Agent node — scores a candidate's answer and feeds the Difficulty Engine."""
from __future__ import annotations

from typing import Any, Dict

from app.agents.difficulty_engine import next_difficulty
from app.agents.prompts.templates import build_evaluation_prompt
from app.agents.schemas import AnswerEvaluation
from app.core.logging import get_logger
from app.infrastructure.azure_openai.client import get_azure_openai_client

logger = get_logger(__name__)


async def evaluation_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    client = get_azure_openai_client()
    system_prompt, user_prompt = build_evaluation_prompt(state)
    evaluation: AnswerEvaluation = await client.generate_structured(system_prompt, user_prompt, AnswerEvaluation)

    state["evaluation_result"] = evaluation.model_dump()

    average = (
        evaluation.technical_score
        + evaluation.communication_score
        + evaluation.confidence_score
        + evaluation.problem_solving_score
    ) / 4

    new_difficulty, adjustment = next_difficulty(state.get("current_difficulty", "intermediate"), average)
    state["current_difficulty"] = new_difficulty
    state["difficulty_adjustment"] = adjustment

    logger.info(
        "answer_evaluated",
        interview_id=state.get("interview_id"),
        average_score=average,
        adjustment=adjustment,
        new_difficulty=new_difficulty,
    )
    return state
