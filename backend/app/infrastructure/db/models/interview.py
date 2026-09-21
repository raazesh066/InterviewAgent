"""Interview + candidate skill models (plain dataclasses; persistence via repositories)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(kw_only=True)
class Interview:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    user_id: Optional[uuid.UUID] = field(default=None, metadata={"kind": "uuid"})
    resume_id: Optional[uuid.UUID] = field(default=None, metadata={"kind": "uuid"})
    candidate_name: str
    category: str
    target_company: str = "Generic"
    interview_type: str
    duration_minutes: int
    years_of_experience: Optional[float] = None
    status: str = "in_progress"
    current_difficulty: str = "intermediate"
    plan: dict = field(default_factory=dict, metadata={"kind": "json"})
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
    completed_at: Optional[datetime] = field(default=None, metadata={"kind": "datetime"})
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})


@dataclass(kw_only=True)
class CandidateSkill:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    interview_id: uuid.UUID = field(metadata={"kind": "uuid"})
    skill_name: str
    level: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
