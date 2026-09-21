"""Unit tests for the weighted scoring framework."""
from types import SimpleNamespace

from app.application.services.scoring_service import compute_final_rating, compute_score_breakdown, grade_for_rating


def _evaluation(**scores):
    defaults = dict(
        technical_score=8, communication_score=8, problem_solving_score=8, confidence_score=8, depth_score=8
    )
    defaults.update(scores)
    return SimpleNamespace(**defaults)


def test_compute_score_breakdown_scales_to_100():
    breakdown = compute_score_breakdown([_evaluation(technical_score=8)])
    assert breakdown["technical_score"] == 80.0


def test_compute_final_rating_applies_weights():
    breakdown = {
        "technical_score": 90,
        "communication_score": 80,
        "problem_solving_score": 80,
        "confidence_score": 70,
        "depth_score": 70,
    }
    # 90*0.4 + 80*0.2 + 80*0.2 + 70*0.1 + 70*0.1 = 36 + 16 + 16 + 7 + 7 = 82
    assert compute_final_rating(breakdown) == 82.0


def test_grade_boundaries():
    assert grade_for_rating(95) == "Outstanding"
    assert grade_for_rating(85) == "Strong Hire"
    assert grade_for_rating(75) == "Hire"
    assert grade_for_rating(65) == "Borderline"
    assert grade_for_rating(40) == "Needs Improvement"
