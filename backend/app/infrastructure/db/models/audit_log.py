"""Audit log model (plain dataclass; persistence via AuditLogRepository)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(kw_only=True)
class AuditLog:
    id: uuid.UUID = field(default_factory=uuid.uuid4, metadata={"kind": "uuid"})
    user_id: Optional[uuid.UUID] = field(default=None, metadata={"kind": "uuid"})
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict, metadata={"kind": "json"})
    ip_address: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), metadata={"kind": "datetime"})
