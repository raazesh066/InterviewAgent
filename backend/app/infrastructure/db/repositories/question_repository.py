"""Question repository."""
import uuid
from typing import Optional, Sequence

from app.infrastructure.db.models.question import Question
from app.infrastructure.db.repositories.base_repository import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    model = Question
    table_name = "questions"

    async def list_by_interview(self, interview_id: uuid.UUID) -> Sequence[Question]:
        columns = [f.name for f in self._fields()]
        sql = (
            f"SELECT {', '.join(columns)} FROM {self.table_name} "
            "WHERE interview_id = ? ORDER BY sequence_number"
        )
        rows = await self.session.fetchall(sql, (str(interview_id),))
        return [self._row_to_model(row) for row in rows]

    async def count_by_interview(self, interview_id: uuid.UUID) -> int:
        row = await self.session.fetchone(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE interview_id = ?", (str(interview_id),)
        )
        return int(row[0]) if row else 0

    async def get_latest(self, interview_id: uuid.UUID) -> Optional[Question]:
        columns = [f.name for f in self._fields()]
        sql = (
            f"SELECT {', '.join(columns)} FROM {self.table_name} "
            "WHERE interview_id = ? ORDER BY sequence_number DESC"
        )
        rows = await self.session.fetchall(sql, (str(interview_id),))
        return self._row_to_model(rows[0]) if rows else None
