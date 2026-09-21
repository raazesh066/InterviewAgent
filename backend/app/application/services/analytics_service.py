"""Analytics aggregation service — powers the React analytics dashboard."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.application.services.scoring_service import compute_final_rating, compute_score_breakdown
from app.infrastructure.db.repositories.evaluation_repository import EvaluationRepository
from app.infrastructure.db.repositories.interview_repository import InterviewRepository
from app.infrastructure.db.repositories.question_repository import QuestionRepository
from app.infrastructure.db.session import DbSession


class AnalyticsService:
    def __init__(self, session: DbSession):
        self.session = session
        self.interviews = InterviewRepository(session)
        self.questions = QuestionRepository(session)
        self.evaluations = EvaluationRepository(session)

    async def get_analytics(self, interview_id: uuid.UUID) -> Dict[str, Any]:
        interview = await self.interviews.get_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

        questions = {q.id: q for q in await self.questions.list_by_interview(interview_id)}
        evaluations = await self.evaluations.list_by_interview(interview_id)

        # Map evaluation -> question via answer_id is not directly available here, so join through answers.
        from app.infrastructure.db.repositories.answer_repository import AnswerRepository

        answers = {a.id: a for a in await AnswerRepository(self.session).list(interview_id=interview_id)}

        skill_scores: Dict[str, List[float]] = {}
        question_timeline: List[Dict[str, Any]] = []
        confidence_trend: List[float] = []
        score_trend: List[float] = []
        strengths: List[str] = []
        weaknesses: List[str] = []

        for evaluation in evaluations:
            answer = answers.get(evaluation.answer_id)
            question = questions.get(answer.question_id) if answer else None
            avg = (
                float(evaluation.technical_score)
                + float(evaluation.communication_score)
                + float(evaluation.problem_solving_score)
                + float(evaluation.depth_score)
            ) / 4

            if question and question.skill:
                skill_scores.setdefault(question.skill, []).append(float(evaluation.technical_score))

            question_timeline.append(
                {
                    "question_id": str(question.id) if question else "",
                    "asked_at": question.asked_at.isoformat() if question else "",
                    "score": round(avg, 1),
                    "difficulty": question.difficulty if question else "",
                }
            )
            confidence_trend.append(float(evaluation.confidence_score))
            score_trend.append(round(avg, 1))
            strengths.extend(evaluation.strengths or [])
            weaknesses.extend(evaluation.missing_points or [])

        skill_performance = [
            {"skill": skill, "average_score": round(sum(scores) / len(scores), 1)}
            for skill, scores in skill_scores.items()
        ]

        current_score = 0.0
        if evaluations:
            breakdown = compute_score_breakdown(evaluations)
            current_score = compute_final_rating(breakdown)

        total_questions = (interview.plan or {}).get("estimated_questions", 1) or 1
        progress_percent = min(100.0, round(len(questions) / total_questions * 100, 1))

        return {
            "progress_percent": progress_percent,
            "current_score": current_score,
            "skill_performance": skill_performance,
            "strengths": list(dict.fromkeys(strengths))[:10],
            "weaknesses": list(dict.fromkeys(weaknesses))[:10],
            "question_timeline": question_timeline,
            "confidence_trend": confidence_trend,
            "score_trend": score_trend,
        }
