"""Question model (plain dataclass; persistence via QuestionRepository)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(kw_only=True)
class Question:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    interview_id: uuid.UUID = field(metadata={"kind": "uuid"})
    parent_question_id: Optional[uuid.UUID] = field(default=None, metadata={"kind": "uuid"})
    agent_type: str
    skill: Optional[str] = None
    text: str
    difficulty: str
    expected_topics: list = field(default_factory=list, metadata={"kind": "json"})
    is_followup: bool = False
    sequence_number: int
    asked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
