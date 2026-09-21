"""Pydantic schemas used as structured-output contracts for LLM calls (LangGraph nodes)."""
from typing import List, Optional

from pydantic import BaseModel, Field


class GeneratedQuestion(BaseModel):
    """Structured output contract for question-generating agents."""

    question: str = Field(description="The interview question text to ask the candidate")
    difficulty: str = Field(description="One of: beginner, intermediate, advanced, expert")
    skill: str = Field(description="Primary skill this question targets")
    expected_topics: List[str] = Field(default_factory=list, description="Key concepts a strong answer should cover")


class AnswerEvaluation(BaseModel):
    """Structured output contract for the Evaluation Agent."""

    technical_score: float = Field(ge=1, le=10)
    communication_score: float = Field(ge=1, le=10)
    confidence_score: float = Field(ge=1, le=10)
    problem_solving_score: float = Field(ge=1, le=10)
    depth_score: float = Field(ge=1, le=10)
    completeness_score: float = Field(ge=1, le=10, default=5)
    missing_points: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    followup_question: Optional[str] = Field(default=None, description="A natural follow-up question, or null")


class FeedbackReport(BaseModel):
    """Structured output contract for the Feedback Agent (final report generation)."""

    executive_summary: str
    strengths: List[str]
    weaknesses: List[str]
    learning_path: List[str]
    communication_assessment: str
    technical_assessment: str
    behavioral_assessment: str
    hiring_recommendation: str
    sample_ideal_answers: List[dict] = Field(
        default_factory=list, description="[{question, ideal_answer}] for the weakest-scoring questions"
    )
