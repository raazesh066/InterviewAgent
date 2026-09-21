"""User model (plain dataclass; persistence via UserRepository — see db/repositories)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(kw_only=True)
class User:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    email: str
    hashed_password: str
    full_name: str
    role: str = "candidate"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
