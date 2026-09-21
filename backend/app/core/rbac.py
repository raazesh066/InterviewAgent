"""Role-based access control dependencies for FastAPI routes."""
import uuid
from enum import Enum
from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.infrastructure.db.session import DbSession, get_db_session

bearer_scheme = HTTPBearer(auto_error=True)


class Role(str, Enum):
    CANDIDATE = "candidate"
    INTERVIEWER = "interviewer"
    ADMIN = "admin"


class CurrentUser:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: DbSession = Depends(get_db_session),
) -> CurrentUser:
    try:
        payload = decode_token(credentials.credentials)
        user_id = uuid.UUID(payload.sub)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if payload.token_type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user = await UserRepository(session).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is no longer valid. Please sign in again.")
    return CurrentUser(user_id=str(user.id), role=user.role)


def require_roles(*allowed_roles: Iterable[Role]):
    """Dependency factory enforcing that the current user has one of the allowed roles."""

    allowed = {r.value if isinstance(r, Role) else r for r in allowed_roles}

    def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed and current_user.role != Role.ADMIN.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _dependency
