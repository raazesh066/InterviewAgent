"""Analytics dashboard endpoint."""
import uuid

from fastapi import APIRouter, Depends, Query

from app.application.services.analytics_service import AnalyticsService
from app.core.rbac import CurrentUser, get_current_user
from app.infrastructure.db.session import DbSession, get_db_session
from app.schemas.analytics_schemas import AnalyticsResponse

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    interview_id: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    service = AnalyticsService(session)
    result = await service.get_analytics(uuid.UUID(interview_id))
    return AnalyticsResponse(**result)
