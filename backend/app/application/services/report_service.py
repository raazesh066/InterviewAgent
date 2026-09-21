"""Final interview report generation service (Feedback Agent + PDF rendering)."""
from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import HTTPException, status

from app.agents.graph import build_feedback_graph
from app.application.services.analytics_service import AnalyticsService
from app.application.services.scoring_service import compute_final_rating, compute_score_breakdown, grade_for_rating
from app.infrastructure.db.models.report import Report
from app.infrastructure.db.repositories.evaluation_repository import EvaluationRepository
from app.infrastructure.db.repositories.interview_repository import CandidateSkillRepository, InterviewRepository
from app.infrastructure.db.repositories.report_repository import ReportRepository
from app.infrastructure.db.session import DbSession
from app.infrastructure.pdf.report_generator import generate_report_pdf
from app.infrastructure.storage import save_file


class ReportService:
    def __init__(self, session: DbSession):
        self.session = session
        self.interviews = InterviewRepository(session)
        self.candidate_skills = CandidateSkillRepository(session)
        self.evaluations = EvaluationRepository(session)
        self.reports = ReportRepository(session)
        self.analytics = AnalyticsService(session)

    async def _build_history_for_feedback(self, interview_id: uuid.UUID):
        from app.application.services.interview_service import InterviewService

        # Reuse the interview service's history builder to avoid duplicating join logic.
        return await InterviewService(self.session)._build_history(interview_id)

    async def build_report_payload(self, interview_id: uuid.UUID) -> Dict[str, Any]:
        interview = await self.interviews.get_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

        existing = await self.reports.get_by_interview(interview_id)
        evaluations = await self.evaluations.list_by_interview(interview_id)
        if not evaluations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate a report before any answers were evaluated"
            )

        breakdown = compute_score_breakdown(evaluations)
        rating = compute_final_rating(breakdown)
        grade = grade_for_rating(rating)
        analytics = await self.analytics.get_analytics(interview_id)

        if existing and abs(float(existing.final_rating or 0) - rating) < 0.01:
            feedback = {
                "executive_summary": existing.executive_summary,
                "strengths": existing.strengths,
                "weaknesses": existing.weaknesses,
                "learning_path": existing.learning_path,
                "communication_assessment": "",
                "technical_assessment": "",
                "behavioral_assessment": "",
                "hiring_recommendation": existing.hiring_recommendation,
                "sample_ideal_answers": existing.ideal_answers,
            }
        else:
            history = await self._build_history_for_feedback(interview_id)
            graph_state = {
                "interview_id": str(interview.id),
                "candidate_name": interview.candidate_name,
                "category": interview.category,
                "target_company": interview.target_company,
                "interview_type": interview.interview_type,
                "history": history,
            }
            feedback_graph = build_feedback_graph()
            result_state = await feedback_graph.ainvoke(graph_state)
            feedback = result_state["feedback_result"]

            report = existing or Report(id=uuid.uuid4(), interview_id=interview_id)
            report.final_rating = rating
            report.grade = grade
            report.executive_summary = feedback["executive_summary"]
            report.strengths = feedback["strengths"]
            report.weaknesses = feedback["weaknesses"]
            report.learning_path = feedback["learning_path"]
            report.ideal_answers = feedback["sample_ideal_answers"]
            report.hiring_recommendation = feedback["hiring_recommendation"]
            if existing:
                await self.reports.update(report)
            else:
                await self.reports.add(report)
            await self.session.commit()

        return {
            "interview_id": str(interview_id),
            "candidate_name": interview.candidate_name,
            "category": interview.category,
            "target_company": interview.target_company,
            "executive_summary": feedback["executive_summary"],
            "final_rating": rating,
            "grade": grade,
            "skill_scorecard": analytics["skill_performance"],
            "communication_assessment": feedback["communication_assessment"],
            "technical_assessment": feedback["technical_assessment"],
            "behavioral_assessment": feedback["behavioral_assessment"],
            "areas_of_improvement": feedback["weaknesses"],
            "learning_path": feedback["learning_path"],
            "sample_ideal_answers": feedback["sample_ideal_answers"],
            "hiring_recommendation": feedback["hiring_recommendation"],
        }

    async def build_report_pdf(self, interview_id: uuid.UUID) -> bytes:
        payload = await self.build_report_payload(interview_id)
        pdf_bytes = generate_report_pdf(payload)
        path = save_file("reports", f"report_{interview_id}.pdf", pdf_bytes)

        report = await self.reports.get_by_interview(interview_id)
        if report:
            report.pdf_storage_path = path
            await self.reports.update(report)
            await self.session.commit()
        return pdf_bytes
