"""Core Interview Orchestration application service.

Coordinates the LangGraph question/evaluation graphs with persistence (repository
pattern) to implement the full interview lifecycle described in the API contract.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.agents.graph import build_evaluation_graph, build_question_graph
from app.agents.orchestrator import build_stage_plan
from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.enums.enums import InterviewStatus
from app.infrastructure.db.models.answer import Answer
from app.infrastructure.db.models.evaluation import Evaluation
from app.infrastructure.db.models.interview import CandidateSkill, Interview
from app.infrastructure.db.models.question import Question
from app.infrastructure.db.repositories.answer_repository import AnswerRepository
from app.infrastructure.db.repositories.evaluation_repository import EvaluationRepository
from app.infrastructure.db.repositories.interview_repository import CandidateSkillRepository, InterviewRepository
from app.infrastructure.db.repositories.question_repository import QuestionRepository
from app.infrastructure.db.repositories.resume_repository import ResumeRepository
from app.infrastructure.db.session import DbSession

logger = get_logger(__name__)

_LEVEL_TO_DIFFICULTY = {
    "Beginner": "beginner",
    "Intermediate": "intermediate",
    "Advanced": "advanced",
    "Expert": "expert",
}
_DIFFICULTY_ORDER = ["beginner", "intermediate", "advanced", "expert"]


def _compute_initial_difficulty(skills: List[Dict[str, str]]) -> str:
    if not skills:
        return "intermediate"
    indices = [_DIFFICULTY_ORDER.index(_LEVEL_TO_DIFFICULTY.get(s["level"], "intermediate")) for s in skills]
    avg_idx = round(sum(indices) / len(indices))
    return _DIFFICULTY_ORDER[max(0, min(len(_DIFFICULTY_ORDER) - 1, avg_idx))]


class InterviewService:
    def __init__(self, session: DbSession):
        self.session = session
        self.interviews = InterviewRepository(session)
        self.candidate_skills = CandidateSkillRepository(session)
        self.questions = QuestionRepository(session)
        self.answers = AnswerRepository(session)
        self.evaluations = EvaluationRepository(session)
        self.resumes = ResumeRepository(session)
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _build_resume_context(self, resume_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not resume_id:
            return None
        resume = await self.resumes.get_by_id(uuid.UUID(resume_id))
        if not resume:
            return None
        return {
            "skills": resume.extracted_skills,
            "projects": resume.extracted_projects,
            "certifications": resume.certifications,
            "education": resume.education,
        }

    async def _build_history(self, interview_id: uuid.UUID) -> List[Dict[str, Any]]:
        questions = await self.questions.list_by_interview(interview_id)
        evaluations = {e.answer_id: e for e in await self.evaluations.list_by_interview(interview_id)}
        answers = {a.question_id: a for a in await self.answers.list(interview_id=interview_id)}

        history: List[Dict[str, Any]] = []
        for q in questions:
            answer = answers.get(q.id)
            entry: Dict[str, Any] = {
                "question": q.text,
                "skill": q.skill,
                "difficulty": q.difficulty,
                "agent_type": q.agent_type,
            }
            if answer:
                entry["answer"] = answer.answer_text or ""
                evaluation = evaluations.get(answer.id)
                if evaluation:
                    entry.update(
                        technical_score=float(evaluation.technical_score),
                        communication_score=float(evaluation.communication_score),
                        confidence_score=float(evaluation.confidence_score),
                        problem_solving_score=float(evaluation.problem_solving_score),
                        depth_score=float(evaluation.depth_score),
                    )
            history.append(entry)
        return history

    def _question_to_response(self, question: Question) -> Dict[str, Any]:
        return {
            "question_id": str(question.id),
            "text": question.text,
            "skill": question.skill,
            "difficulty": question.difficulty,
            "type": question.agent_type,
            "expected_topics": question.expected_topics or [],
            "is_followup": question.is_followup,
        }

    async def _elapsed_minutes(self, interview: Interview) -> float:
        started = interview.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - started).total_seconds() / 60.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def start_interview(self, user_id: Optional[uuid.UUID], payload) -> Dict[str, Any]:
        skills = [{"name": s.name, "level": s.level.value} for s in payload.skills]
        resume_context = await self._build_resume_context(payload.resume_id)
        initial_difficulty = _compute_initial_difficulty(skills)
        stage_plan = build_stage_plan(payload.interview_type.value)
        estimated_questions = min(
            self.settings.max_questions_per_interview, max(3, payload.duration_minutes // 5)
        )

        interview = Interview(
            id=uuid.uuid4(),
            user_id=user_id,
            resume_id=uuid.UUID(payload.resume_id) if payload.resume_id else None,
            candidate_name=payload.candidate_name,
            category=payload.category.value,
            target_company=payload.target_company.value,
            interview_type=payload.interview_type.value,
            duration_minutes=payload.duration_minutes,
            years_of_experience=payload.years_of_experience,
            status=InterviewStatus.IN_PROGRESS.value,
            current_difficulty=initial_difficulty,
            plan={"stages": stage_plan, "estimated_questions": estimated_questions},
        )
        interview = await self.interviews.add(interview)

        for s in skills:
            await self.candidate_skills.add(
                CandidateSkill(id=uuid.uuid4(), interview_id=interview.id, skill_name=s["name"], level=s["level"])
            )

        graph_state: Dict[str, Any] = {
            "interview_id": str(interview.id),
            "category": interview.category,
            "interview_type": interview.interview_type,
            "target_company": interview.target_company,
            "years_of_experience": float(interview.years_of_experience or 0),
            "skills": skills,
            "resume_context": resume_context,
            "stage_plan": stage_plan,
            "current_difficulty": initial_difficulty,
            "question_count": 0,
            "max_questions": estimated_questions,
            "history": [],
        }

        question_graph = build_question_graph()
        result_state = await question_graph.ainvoke(graph_state)
        generated = result_state["generated_question"]

        question = Question(
            id=uuid.uuid4(),
            interview_id=interview.id,
            agent_type=generated["agent_type"],
            skill=generated.get("skill"),
            text=generated["question"],
            difficulty=generated.get("difficulty", initial_difficulty),
            expected_topics=generated.get("expected_topics", []),
            is_followup=False,
            sequence_number=1,
        )
        question = await self.questions.add(question)
        await self.session.commit()

        return {
            "interview_id": str(interview.id),
            "status": interview.status,
            "plan": {"stages": stage_plan, "estimated_questions": estimated_questions},
            "first_question": self._question_to_response(question),
        }

    async def submit_answer(self, payload) -> Dict[str, Any]:
        interview = await self.interviews.get_by_id(uuid.UUID(payload.interview_id))
        if not interview:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
        question = await self.questions.get_by_id(uuid.UUID(payload.question_id))
        if not question or question.interview_id != interview.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        answer = Answer(
            id=uuid.uuid4(),
            question_id=question.id,
            interview_id=interview.id,
            answer_text=payload.answer_text,
            time_taken_seconds=payload.time_taken_seconds,
        )
        answer = await self.answers.add(answer)

        history = await self._build_history(interview.id)
        skills = [
            {"name": s.skill_name, "level": s.level} for s in await self.candidate_skills.list_by_interview(interview.id)
        ]

        graph_state: Dict[str, Any] = {
            "interview_id": str(interview.id),
            "category": interview.category,
            "interview_type": interview.interview_type,
            "target_company": interview.target_company,
            "years_of_experience": float(interview.years_of_experience or 0),
            "skills": skills,
            "current_difficulty": interview.current_difficulty,
            "history": history,
            "candidate_answer": payload.answer_text,
            "last_question": self._question_to_response(question),
        }

        evaluation_graph = build_evaluation_graph()
        result_state = await evaluation_graph.ainvoke(graph_state)
        eval_result = result_state["evaluation_result"]
        adjustment = result_state["difficulty_adjustment"]
        new_difficulty = result_state["current_difficulty"]

        evaluation = Evaluation(
            id=uuid.uuid4(),
            answer_id=answer.id,
            interview_id=interview.id,
            technical_score=eval_result["technical_score"],
            communication_score=eval_result["communication_score"],
            confidence_score=eval_result["confidence_score"],
            problem_solving_score=eval_result["problem_solving_score"],
            depth_score=eval_result["depth_score"],
            completeness_score=eval_result.get("completeness_score"),
            missing_points=eval_result.get("missing_points", []),
            strengths=eval_result.get("strengths", []),
            followup_question=eval_result.get("followup_question"),
            difficulty_adjustment=adjustment,
        )
        await self.evaluations.add(evaluation)
        await self.interviews.update_difficulty(interview.id, new_difficulty)

        # Determine if the interview should end (time or question-count exhausted)
        elapsed = await self._elapsed_minutes(interview)
        question_count = await self.questions.count_by_interview(interview.id)
        max_questions = (interview.plan or {}).get("estimated_questions", self.settings.max_questions_per_interview)
        interview_status = interview.status
        if elapsed >= interview.duration_minutes or question_count >= max_questions:
            await self.interviews.mark_completed(interview.id)
            interview_status = InterviewStatus.COMPLETED.value

        await self.session.commit()

        return {
            "evaluation": {
                "technical_score": eval_result["technical_score"],
                "communication_score": eval_result["communication_score"],
                "confidence_score": eval_result["confidence_score"],
                "problem_solving_score": eval_result["problem_solving_score"],
                "depth_score": eval_result["depth_score"],
                "missing_points": eval_result.get("missing_points", []),
                "strengths": eval_result.get("strengths", []),
                "followup_question": eval_result.get("followup_question"),
            },
            "difficulty_adjustment": adjustment,
            "interview_status": interview_status,
        }

    async def get_next_question(self, interview_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        interview = await self.interviews.get_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

        if interview.status == InterviewStatus.COMPLETED.value:
            return None

        elapsed = await self._elapsed_minutes(interview)
        question_count = await self.questions.count_by_interview(interview.id)
        max_questions = (interview.plan or {}).get("estimated_questions", self.settings.max_questions_per_interview)
        if elapsed >= interview.duration_minutes or question_count >= max_questions:
            await self.interviews.mark_completed(interview.id)
            await self.session.commit()
            return None

        # Prefer an unconsumed follow-up question from the most recent evaluation.
        evaluations = await self.evaluations.list_by_interview(interview.id)
        last_question = await self.questions.get_latest(interview.id)
        if evaluations:
            latest_eval = evaluations[-1]
            if latest_eval.followup_question:
                followup_text = latest_eval.followup_question
                latest_eval.followup_question = None  # mark as consumed
                await self.evaluations.update(latest_eval)

                question = Question(
                    id=uuid.uuid4(),
                    interview_id=interview.id,
                    parent_question_id=last_question.id if last_question else None,
                    agent_type=last_question.agent_type if last_question else "technical",
                    skill=last_question.skill if last_question else None,
                    text=followup_text,
                    difficulty=interview.current_difficulty,
                    expected_topics=[],
                    is_followup=True,
                    sequence_number=question_count + 1,
                )
                question = await self.questions.add(question)
                await self.session.commit()
                return self._question_to_response(question)

        history = await self._build_history(interview.id)
        skills = [
            {"name": s.skill_name, "level": s.level} for s in await self.candidate_skills.list_by_interview(interview.id)
        ]
        resume_context = await self._build_resume_context(str(interview.resume_id) if interview.resume_id else None)

        graph_state: Dict[str, Any] = {
            "interview_id": str(interview.id),
            "category": interview.category,
            "interview_type": interview.interview_type,
            "target_company": interview.target_company,
            "years_of_experience": float(interview.years_of_experience or 0),
            "skills": skills,
            "resume_context": resume_context,
            "stage_plan": (interview.plan or {}).get("stages", build_stage_plan(interview.interview_type)),
            "current_difficulty": interview.current_difficulty,
            "question_count": question_count,
            "max_questions": max_questions,
            "history": history,
        }

        question_graph = build_question_graph()
        result_state = await question_graph.ainvoke(graph_state)
        generated = result_state["generated_question"]

        question = Question(
            id=uuid.uuid4(),
            interview_id=interview.id,
            agent_type=generated["agent_type"],
            skill=generated.get("skill"),
            text=generated["question"],
            difficulty=generated.get("difficulty", interview.current_difficulty),
            expected_topics=generated.get("expected_topics", []),
            is_followup=False,
            sequence_number=question_count + 1,
        )
        question = await self.questions.add(question)
        await self.session.commit()
        return self._question_to_response(question)

    async def get_score(self, interview_id: uuid.UUID) -> Dict[str, Any]:
        from app.application.services.scoring_service import compute_final_rating, compute_score_breakdown, grade_for_rating, WEIGHTS

        evaluations = await self.evaluations.list_by_interview(interview_id)
        if not evaluations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No evaluations yet for this interview")

        breakdown = compute_score_breakdown(evaluations)
        rating = compute_final_rating(breakdown)
        grade = grade_for_rating(rating)
        return {"final_rating": rating, "grade": grade, "breakdown": breakdown, "weights": WEIGHTS}
