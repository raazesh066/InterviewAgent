"""Report + Analytics models (plain dataclasses; persistence via ReportRepository)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(kw_only=True)
class Report:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    interview_id: uuid.UUID = field(metadata={"kind": "uuid"})
    final_rating: Optional[float] = None
    grade: Optional[str] = None
    executive_summary: Optional[str] = None
    strengths: list = field(default_factory=list, metadata={"kind": "json"})
    weaknesses: list = field(default_factory=list, metadata={"kind": "json"})
    learning_path: list = field(default_factory=list, metadata={"kind": "json"})
    ideal_answers: list = field(default_factory=list, metadata={"kind": "json"})
    hiring_recommendation: Optional[str] = None
    pdf_storage_path: Optional[str] = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})


@dataclass(kw_only=True)
class Analytics:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    interview_id: uuid.UUID = field(metadata={"kind": "uuid"})
    skill_performance: list = field(default_factory=list, metadata={"kind": "json"})
    confidence_trend: list = field(default_factory=list, metadata={"kind": "json"})
    score_trend: list = field(default_factory=list, metadata={"kind": "json"})
    question_timeline: list = field(default_factory=list, metadata={"kind": "json"})
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
