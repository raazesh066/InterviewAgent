"""Final report endpoint (JSON or downloadable PDF)."""
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.application.services.audit_service import AuditService
from app.application.services.report_service import ReportService
from app.core.rbac import CurrentUser, get_current_user
from app.infrastructure.db.session import DbSession, get_db_session
from app.schemas.analytics_schemas import ReportResponse

router = APIRouter(tags=["report"])


@router.get("/report")
async def get_report(
    interview_id: str = Query(...),
    format: str = Query(default="json", pattern="^(json|pdf)$"),
    current_user: CurrentUser = Depends(get_current_user),
    session: DbSession = Depends(get_db_session),
):
    service = ReportService(session)

    if format == "pdf":
        pdf_bytes = await service.build_report_pdf(uuid.UUID(interview_id))
        await AuditService(session).record(
            uuid.UUID(current_user.user_id), "report.download_pdf", resource="interview", resource_id=interview_id
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=interview_report_{interview_id}.pdf"},
        )

    payload = await service.build_report_payload(uuid.UUID(interview_id))
    return ReportResponse(**payload)
