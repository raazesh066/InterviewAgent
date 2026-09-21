"""Evaluation model (plain dataclass; persistence via EvaluationRepository)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(kw_only=True)
class Evaluation:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    answer_id: uuid.UUID = field(metadata={"kind": "uuid"})
    interview_id: uuid.UUID = field(metadata={"kind": "uuid"})
    technical_score: float
    communication_score: float
    confidence_score: float
    problem_solving_score: float
    depth_score: float
    completeness_score: Optional[float] = None
    missing_points: list = field(default_factory=list, metadata={"kind": "json"})
    strengths: list = field(default_factory=list, metadata={"kind": "json"})
    followup_question: Optional[str] = None
    difficulty_adjustment: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
