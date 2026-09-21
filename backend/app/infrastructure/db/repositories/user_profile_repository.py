"""Candidate profile persistence and account-level interview statistics."""
import dataclasses
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.infrastructure.db.models.types import deserialize_value, serialize_value
from app.infrastructure.db.models.user_profile import UserProfile
from app.infrastructure.db.session import DbSession


class UserProfileRepository:
    def __init__(self, session: DbSession):
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserProfile]:
        fields = dataclasses.fields(UserProfile)
        columns = [item.name for item in fields]
        row = await self.session.fetchone(
            f"SELECT {', '.join(columns)} FROM user_profiles WHERE user_id = ?",
            (str(user_id),),
        )
        if not row:
            return None
        values = {
            item.name: deserialize_value(value, item.metadata.get("kind"))
            for item, value in zip(fields, row)
        }
        return UserProfile(**values)

    async def save(self, profile: UserProfile) -> UserProfile:
        existing = await self.get_by_user_id(profile.user_id)
        profile.updated_at = datetime.now(timezone.utc)
        if existing:
            await self.session.execute(
                """UPDATE user_profiles SET headline = ?, target_role = ?, years_of_experience = ?,
                location = ?, bio = ?, skills = ?, preferred_company = ?,
                preferred_interview_type = ?, updated_at = ? WHERE user_id = ?""",
                (
                    profile.headline,
                    profile.target_role,
                    profile.years_of_experience,
                    profile.location,
                    profile.bio,
                    serialize_value(profile.skills),
                    profile.preferred_company,
                    profile.preferred_interview_type,
                    serialize_value(profile.updated_at),
                    str(profile.user_id),
                ),
            )
        else:
            await self.session.execute(
                """INSERT INTO user_profiles
                (user_id, headline, target_role, years_of_experience, location, bio, skills,
                preferred_company, preferred_interview_type, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(profile.user_id),
                    profile.headline,
                    profile.target_role,
                    profile.years_of_experience,
                    profile.location,
                    profile.bio,
                    serialize_value(profile.skills),
                    profile.preferred_company,
                    profile.preferred_interview_type,
                    serialize_value(profile.updated_at),
                ),
            )
        return profile

    async def interview_counts(self, user_id: uuid.UUID) -> tuple[int, int]:
        row = await self.session.fetchone(
            """SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
            FROM interviews WHERE user_id = ?""",
            (str(user_id),),
        )
        return (int(row[0] or 0), int(row[1] or 0)) if row else (0, 0)