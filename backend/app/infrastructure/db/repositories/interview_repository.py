"""Interview + candidate skill repositories."""
import uuid
from datetime import datetime, timezone
from typing import Sequence

from app.infrastructure.db.models.interview import CandidateSkill, Interview
from app.infrastructure.db.repositories.base_repository import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    model = Interview
    table_name = "interviews"

    async def update_status(self, interview_id: uuid.UUID, status: str) -> None:
        await self.session.execute(
            f"UPDATE {self.table_name} SET status = ? WHERE id = ?", (status, str(interview_id))
        )

    async def update_difficulty(self, interview_id: uuid.UUID, difficulty: str) -> None:
        await self.session.execute(
            f"UPDATE {self.table_name} SET current_difficulty = ? WHERE id = ?",
            (difficulty, str(interview_id)),
        )

    async def mark_completed(self, interview_id: uuid.UUID) -> None:
        await self.session.execute(
            f"UPDATE {self.table_name} SET status = ?, completed_at = ? WHERE id = ?",
            ("completed", datetime.now(timezone.utc).isoformat(), str(interview_id)),
        )


class CandidateSkillRepository(BaseRepository[CandidateSkill]):
    model = CandidateSkill
    table_name = "candidate_skills"

    async def list_by_interview(self, interview_id: uuid.UUID) -> Sequence[CandidateSkill]:
        return await self.list(interview_id=interview_id)
