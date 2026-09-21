"""Analytics + report response schemas."""
from typing import Any, Dict, List

from pydantic import BaseModel


class SkillPerformance(BaseModel):
    skill: str
    average_score: float


class QuestionTimelineEntry(BaseModel):
    question_id: str
    asked_at: str
    score: float
    difficulty: str


class AnalyticsResponse(BaseModel):
    progress_percent: float
    current_score: float
    skill_performance: List[SkillPerformance]
    strengths: List[str]
    weaknesses: List[str]
    question_timeline: List[QuestionTimelineEntry]
    confidence_trend: List[float]
    score_trend: List[float]


class ReportResponse(BaseModel):
    interview_id: str
    executive_summary: str
    final_rating: float
    grade: str
    skill_scorecard: List[SkillPerformance]
    communication_assessment: str
    technical_assessment: str
    behavioral_assessment: str
    areas_of_improvement: List[str]
    learning_path: List[str]
    sample_ideal_answers: List[Dict[str, Any]]
    hiring_recommendation: str
