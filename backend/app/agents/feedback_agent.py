"""Feedback Agent node — produces the final structured report content."""
from __future__ import annotations

from typing import Any, Dict

from app.agents.prompts.templates import build_feedback_prompt
from app.agents.schemas import FeedbackReport
from app.core.logging import get_logger
from app.infrastructure.azure_openai.client import get_azure_openai_client

logger = get_logger(__name__)


async def feedback_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    client = get_azure_openai_client()
    system_prompt, user_prompt = build_feedback_prompt(state)
    feedback: FeedbackReport = await client.generate_structured(system_prompt, user_prompt, FeedbackReport)
    state["feedback_result"] = feedback.model_dump()
    logger.info("feedback_generated", interview_id=state.get("interview_id"))
    return state
