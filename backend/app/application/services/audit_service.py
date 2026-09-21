"""Audit logging application service — records sensitive actions for compliance."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from app.infrastructure.db.models.audit_log import AuditLog
from app.infrastructure.db.repositories.audit_log_repository import AuditLogRepository
from app.infrastructure.db.session import DbSession


class AuditService:
    def __init__(self, session: DbSession):
        self.session = session
        self.repo = AuditLogRepository(session)

    async def record(
        self,
        user_id: Optional[uuid.UUID],
        action: str,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            metadata=metadata or {},
            ip_address=ip_address,
        )
        await self.repo.add(log)
        await self.session.commit()
