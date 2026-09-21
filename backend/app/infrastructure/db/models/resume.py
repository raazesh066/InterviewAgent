"""Resume model (plain dataclass; persistence via ResumeRepository — see db/repositories)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(kw_only=True)
class Resume:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    user_id: Optional[uuid.UUID] = field(default=None, metadata={"kind": "uuid"})
    file_name: str
    storage_path: str
    raw_text: Optional[str] = None
    extracted_skills: list = field(default_factory=list, metadata={"kind": "json"})
    extracted_projects: list = field(default_factory=list, metadata={"kind": "json"})
    experience_years: Optional[float] = None
    certifications: list = field(default_factory=list, metadata={"kind": "json"})
    education: list = field(default_factory=list, metadata={"kind": "json"})
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
