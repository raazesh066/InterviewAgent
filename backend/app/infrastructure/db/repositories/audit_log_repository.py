"""Audit log repository."""
from app.infrastructure.db.models.audit_log import AuditLog
from app.infrastructure.db.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog
    table_name = "audit_logs"
