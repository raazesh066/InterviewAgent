"""Resume upload endpoint."""
import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.application.services.audit_service import AuditService
from app.application.services.resume_service import ResumeService
from app.core.rate_limit import limiter
from app.core.rbac import CurrentUser, get_current_user
from app.infrastructure.db.session import DbSession, get_db_session
from app.schemas.resume_schemas import ResumeUploadResponse

router = APIRouter(tags=["resume"])


@router.post("/upload-resume", response_model=ResumeUploadResponse, status_code=201)
@limiter.limit("10/minute")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    content = await file.read()
    service = ResumeService(session)
    resume, parsed = await service.upload_and_parse(uuid.UUID(current_user.user_id), file.filename, content)

    await AuditService(session).record(
        uuid.UUID(current_user.user_id), "resume.upload", resource="resume", resource_id=str(resume.id)
    )

    return ResumeUploadResponse(resume_id=str(resume.id), file_name=resume.file_name, parsed=parsed)
