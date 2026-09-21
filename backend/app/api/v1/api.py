"""Aggregates all v1 routers under a single APIRouter."""
from fastapi import APIRouter

from app.api.v1.routers import (
    analytics_router,
    auth_router,
    interview_router,
    report_router,
    resume_router,
    voice_router,
)

api_router = APIRouter()
api_router.include_router(auth_router.router)
api_router.include_router(resume_router.router)
api_router.include_router(interview_router.router)
api_router.include_router(analytics_router.router)
api_router.include_router(report_router.router)
api_router.include_router(voice_router.router)
