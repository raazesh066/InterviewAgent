"""Evaluation repository."""
import uuid
from typing import Sequence

from app.infrastructure.db.models.evaluation import Evaluation
from app.infrastructure.db.repositories.base_repository import BaseRepository


class EvaluationRepository(BaseRepository[Evaluation]):
    model = Evaluation
    table_name = "evaluations"

    async def list_by_interview(self, interview_id: uuid.UUID) -> Sequence[Evaluation]:
        columns = [f.name for f in self._fields()]
        sql = (
            f"SELECT {', '.join(columns)} FROM {self.table_name} "
            "WHERE interview_id = ? ORDER BY created_at"
        )
        rows = await self.session.fetchall(sql, (str(interview_id),))
        return [self._row_to_model(row) for row in rows]
