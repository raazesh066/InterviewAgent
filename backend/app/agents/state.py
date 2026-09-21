"""Shared LangGraph state definitions for the interview multi-agent system."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class QAHistoryEntry(TypedDict, total=False):
    question: str
    skill: str
    difficulty: str
    agent_type: str
    answer: str
    technical_score: float
    communication_score: float
    confidence_score: float
    problem_solving_score: float
    depth_score: float


class InterviewGraphState(TypedDict, total=False):
    """State threaded through the LangGraph question-generation / evaluation graphs.

    Populated from the DB before invoking a graph, and read back afterwards by the
    application service layer to persist results.
    """

    interview_id: str
    category: str
    interview_type: str
    target_company: str
    years_of_experience: float
    skills: List[Dict[str, str]]  # [{name, level}]
    resume_context: Optional[Dict[str, Any]]
    stage_plan: List[str]
    current_stage_index: int
    current_difficulty: str
    question_count: int
    max_questions: int
    history: List[QAHistoryEntry]

    # Routing
    next_agent: Optional[str]

    # Question generation I/O
    generated_question: Optional[Dict[str, Any]]

    # Evaluation I/O
    candidate_answer: Optional[str]
    last_question: Optional[Dict[str, Any]]
    evaluation_result: Optional[Dict[str, Any]]
    difficulty_adjustment: Optional[str]

    # Feedback I/O
    feedback_result: Optional[Dict[str, Any]]
