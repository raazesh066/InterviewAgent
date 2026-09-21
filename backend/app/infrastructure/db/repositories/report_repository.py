"""Report + Analytics repositories."""
import uuid
from typing import Optional

from app.infrastructure.db.models.report import Analytics, Report
from app.infrastructure.db.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report
    table_name = "reports"

    async def get_by_interview(self, interview_id: uuid.UUID) -> Optional[Report]:
        columns = [f.name for f in self._fields()]
        sql = f"SELECT {', '.join(columns)} FROM {self.table_name} WHERE interview_id = ?"
        row = await self.session.fetchone(sql, (str(interview_id),))
        return self._row_to_model(row) if row else None


class AnalyticsRepository(BaseRepository[Analytics]):
    model = Analytics
    table_name = "analytics"

    async def get_by_interview(self, interview_id: uuid.UUID) -> Optional[Analytics]:
        columns = [f.name for f in self._fields()]
        sql = f"SELECT {', '.join(columns)} FROM {self.table_name} WHERE interview_id = ?"
        row = await self.session.fetchone(sql, (str(interview_id),))
        return self._row_to_model(row) if row else None

    async def upsert(self, interview_id: uuid.UUID, **fields) -> Analytics:
        existing = await self.get_by_interview(interview_id)
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            await self.update(existing)
            return existing
        analytics = Analytics(interview_id=interview_id, **fields)
        return await self.add(analytics)
