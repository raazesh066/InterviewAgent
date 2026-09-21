"""Weighted scoring framework: converts per-answer evaluations into the final rating/grade."""
from __future__ import annotations

from typing import Iterable, Sequence

from app.domain.enums.enums import Grade

WEIGHTS = {
    "technical": 0.40,
    "communication": 0.20,
    "problem_solving": 0.20,
    "confidence": 0.10,
    "depth": 0.10,
}


def _avg(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_score_breakdown(evaluations: Iterable) -> dict:
    """Given an iterable of evaluation-like objects with score attributes (1-10 scale),
    return the per-dimension average rescaled to 0-100.
    """
    evaluations = list(evaluations)
    technical = _avg([float(e.technical_score) for e in evaluations]) * 10
    communication = _avg([float(e.communication_score) for e in evaluations]) * 10
    problem_solving = _avg([float(e.problem_solving_score) for e in evaluations]) * 10
    confidence = _avg([float(e.confidence_score) for e in evaluations]) * 10
    depth = _avg([float(e.depth_score) for e in evaluations]) * 10

    return {
        "technical_score": round(technical, 1),
        "communication_score": round(communication, 1),
        "problem_solving_score": round(problem_solving, 1),
        "confidence_score": round(confidence, 1),
        "depth_score": round(depth, 1),
    }


def compute_final_rating(breakdown: dict) -> float:
    rating = (
        breakdown["technical_score"] * WEIGHTS["technical"]
        + breakdown["communication_score"] * WEIGHTS["communication"]
        + breakdown["problem_solving_score"] * WEIGHTS["problem_solving"]
        + breakdown["confidence_score"] * WEIGHTS["confidence"]
        + breakdown["depth_score"] * WEIGHTS["depth"]
    )
    return round(rating, 2)


def grade_for_rating(rating: float) -> str:
    return Grade.from_score(rating).value
