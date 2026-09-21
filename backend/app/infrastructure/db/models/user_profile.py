"""Candidate profile model."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(kw_only=True)
class UserProfile:
    user_id: uuid.UUID = field(metadata={"kind": "uuid"})
    headline: str = ""
    target_role: str = "Software Engineer"
    years_of_experience: float = 0
    location: str = ""
    bio: str = ""
    skills: list[str] = field(default_factory=list, metadata={"kind": "json"})
    preferred_company: str = "Generic"
    preferred_interview_type: str = "Technical"
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})