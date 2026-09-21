"""Interview lifecycle request/response schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.enums.enums import InterviewCategory, InterviewType, ProficiencyLevel, TargetCompany


class SkillSelection(BaseModel):
    name: str
    level: ProficiencyLevel


class StartInterviewRequest(BaseModel):
    candidate_name: str
    resume_id: Optional[str] = None
    target_company: TargetCompany = TargetCompany.GENERIC
    category: InterviewCategory
    interview_type: InterviewType
    duration_minutes: int = Field(gt=0, le=180)
    years_of_experience: Optional[float] = 0
    skills: List[SkillSelection]


class QuestionResponse(BaseModel):
    question_id: str
    text: str
    skill: Optional[str] = None
    difficulty: str
    type: str
    expected_topics: List[str] = []
    is_followup: bool = False


class InterviewPlan(BaseModel):
    stages: List[str]
    estimated_questions: int


class StartInterviewResponse(BaseModel):
    interview_id: str
    status: str
    plan: InterviewPlan
    first_question: QuestionResponse


class SubmitAnswerRequest(BaseModel):
    interview_id: str
    question_id: str
    answer_text: str
    answer_audio_url: Optional[str] = None
    time_taken_seconds: Optional[int] = None


class EvaluationResult(BaseModel):
    technical_score: float
    communication_score: float
    confidence_score: float
    problem_solving_score: float
    depth_score: float
    missing_points: List[str] = []
    strengths: List[str] = []
    followup_question: Optional[str] = None


class SubmitAnswerResponse(BaseModel):
    evaluation: EvaluationResult
    difficulty_adjustment: str
    interview_status: str


class ScoreBreakdown(BaseModel):
    technical_score: float
    communication_score: float
    problem_solving_score: float
    confidence_score: float
    depth_score: float


class InterviewScoreResponse(BaseModel):
    final_rating: float
    grade: str
    breakdown: ScoreBreakdown
    weights: dict
