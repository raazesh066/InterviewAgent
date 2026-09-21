"""Unit tests for the Dynamic Difficulty Adjustment engine."""
import pytest

from app.agents.difficulty_engine import decide_adjustment, next_difficulty
from app.domain.enums.enums import DifficultyAdjustment


@pytest.mark.parametrize(
    "score,expected",
    [
        (10, DifficultyAdjustment.INCREASE),
        (8, DifficultyAdjustment.INCREASE),
        (7, DifficultyAdjustment.MAINTAIN),
        (5, DifficultyAdjustment.MAINTAIN),
        (4, DifficultyAdjustment.DECREASE),
        (1, DifficultyAdjustment.DECREASE),
    ],
)
def test_decide_adjustment(score, expected):
    assert decide_adjustment(score) == expected


@pytest.mark.parametrize(
    "current,score,expected_difficulty,expected_adjustment",
    [
        ("beginner", 9, "intermediate", "increase"),
        ("expert", 9, "expert", "increase"),  # already at the top, stays capped
        ("intermediate", 6, "intermediate", "maintain"),
        ("advanced", 2, "intermediate", "decrease"),
        ("beginner", 2, "beginner", "decrease"),  # already at the bottom, stays capped
    ],
)
def test_next_difficulty(current, score, expected_difficulty, expected_adjustment):
    new_difficulty, adjustment = next_difficulty(current, score)
    assert new_difficulty == expected_difficulty
    assert adjustment == expected_adjustment
