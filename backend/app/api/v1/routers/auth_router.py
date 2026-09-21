"""Auth endpoints."""
import uuid

from fastapi import APIRouter, Depends, Request

from app.application.services.audit_service import AuditService
from app.application.services.auth_service import AuthService
from app.core.rate_limit import limiter
from app.core.rbac import CurrentUser, get_current_user
from app.infrastructure.db.session import DbSession, get_db_session
from app.schemas.auth_schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, payload: RegisterRequest, session: DbSession = Depends(get_db_session)):
    service = AuthService(session)
    user = await service.register(payload.email, payload.password, payload.full_name)
    await AuditService(session).record(user.id, "user.register", resource="user", resource_id=str(user.id))
    return UserResponse(id=str(user.id), email=user.email, full_name=user.full_name, role=user.role)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(request: Request, payload: LoginRequest, session: DbSession = Depends(get_db_session)):
    service = AuthService(session)
    user = await service.authenticate(payload.email, payload.password)
    tokens = service.issue_tokens(user)
    await AuditService(session).record(user.id, "user.login", resource="user", resource_id=str(user.id))
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, session: DbSession = Depends(get_db_session)):
    service = AuthService(session)
    tokens = await service.refresh(payload.refresh_token)
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    return UserProfileResponse(**await AuthService(session).get_profile(uuid.UUID(current_user.user_id)))


@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    service = AuthService(session)
    profile = await service.update_profile(uuid.UUID(current_user.user_id), payload)
    await AuditService(session).record(
        uuid.UUID(current_user.user_id), "user.profile.update", resource="user", resource_id=current_user.user_id
    )
    return UserProfileResponse(**profile)
