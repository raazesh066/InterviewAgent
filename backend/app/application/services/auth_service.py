"""Authentication application service: register/login/refresh."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.user_profile import UserProfile
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.infrastructure.db.repositories.user_profile_repository import UserProfileRepository
from app.infrastructure.db.session import DbSession


class AuthService:
    def __init__(self, session: DbSession):
        self.session = session
        self.users = UserRepository(session)
        self.profiles = UserProfileRepository(session)

    async def register(self, email: str, password: str, full_name: str) -> User:
        existing = await self.users.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role="candidate",
        )
        user = await self.users.add(user)
        await self.session.commit()
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        return user

    def issue_tokens(self, user: User) -> dict:
        settings = get_settings()
        return {
            "access_token": create_access_token(str(user.id), user.role),
            "refresh_token": create_refresh_token(str(user.id)),
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        if payload.token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user: Optional[User] = await self.users.get_by_id(uuid.UUID(payload.sub))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return self.issue_tokens(user)

    async def get_profile(self, user_id: uuid.UUID) -> dict:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        profile = await self.profiles.get_by_user_id(user_id) or UserProfile(user_id=user_id)
        total_interviews, completed_interviews = await self.profiles.interview_counts(user_id)
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "joined_at": user.created_at,
            "headline": profile.headline,
            "target_role": profile.target_role,
            "years_of_experience": profile.years_of_experience,
            "location": profile.location,
            "bio": profile.bio,
            "skills": profile.skills,
            "preferred_company": profile.preferred_company,
            "preferred_interview_type": profile.preferred_interview_type,
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
        }

    async def update_profile(self, user_id: uuid.UUID, payload) -> dict:
        profile = UserProfile(user_id=user_id, **payload.model_dump())
        await self.profiles.save(profile)
        await self.session.commit()
        return await self.get_profile(user_id)
