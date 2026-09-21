"""Interview lifecycle endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.application.services.audit_service import AuditService
from app.application.services.interview_service import InterviewService
from app.core.rate_limit import limiter
from app.core.rbac import CurrentUser, get_current_user
from app.infrastructure.db.session import DbSession, get_db_session
from app.schemas.interview_schemas import (
    InterviewScoreResponse,
    QuestionResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)

router = APIRouter(tags=["interview"])


@router.post("/start-interview", response_model=StartInterviewResponse, status_code=201)
@limiter.limit("15/minute")
async def start_interview(
    request: Request,
    payload: StartInterviewRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    service = InterviewService(session)
    result = await service.start_interview(uuid.UUID(current_user.user_id), payload)
    await AuditService(session).record(
        uuid.UUID(current_user.user_id),
        "interview.start",
        resource="interview",
        resource_id=result["interview_id"],
    )
    return StartInterviewResponse(**result)


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
@limiter.limit("60/minute")
async def submit_answer(
    request: Request,
    payload: SubmitAnswerRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    service = InterviewService(session)
    result = await service.submit_answer(payload)
    await AuditService(session).record(
        uuid.UUID(current_user.user_id),
        "interview.submit_answer",
        resource="interview",
        resource_id=payload.interview_id,
    )
    return SubmitAnswerResponse(**result)


@router.get("/next-question", response_model=QuestionResponse)
async def next_question(
    response: Response,
    interview_id: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    service = InterviewService(session)
    result = await service.get_next_question(uuid.UUID(interview_id))
    if result is None:
        response.headers["X-Interview-Status"] = "completed"
        return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"X-Interview-Status": "completed"})
    return QuestionResponse(**result)


@router.get("/interview-score", response_model=InterviewScoreResponse)
async def interview_score(
    interview_id: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    service = InterviewService(session)
    result = await service.get_score(uuid.UUID(interview_id))
    return InterviewScoreResponse(**result)
