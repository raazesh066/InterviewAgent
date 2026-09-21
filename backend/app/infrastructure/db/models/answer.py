"""Answer model (plain dataclass; persistence via AnswerRepository)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(kw_only=True)
class Answer:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    question_id: uuid.UUID = field(metadata={"kind": "uuid"})
    interview_id: uuid.UUID = field(metadata={"kind": "uuid"})
    answer_text: Optional[str] = None
    answer_audio_path: Optional[str] = None
    time_taken_seconds: Optional[int] = None
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
