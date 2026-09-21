"""Dynamic Difficulty Adjustment engine.

Score 8-10  -> move to a harder question
Score 5-7   -> maintain current level
Score 1-4   -> ask a simpler question
"""
from app.domain.enums.enums import DifficultyAdjustment, DifficultyLevel


def decide_adjustment(average_score: float) -> DifficultyAdjustment:
    if average_score >= 8:
        return DifficultyAdjustment.INCREASE
    if average_score >= 5:
        return DifficultyAdjustment.MAINTAIN
    return DifficultyAdjustment.DECREASE


def apply_adjustment(current: DifficultyLevel, adjustment: DifficultyAdjustment) -> DifficultyLevel:
    if adjustment == DifficultyAdjustment.INCREASE:
        return current.step(1)
    if adjustment == DifficultyAdjustment.DECREASE:
        return current.step(-1)
    return current


def next_difficulty(current_difficulty: str, average_score: float) -> tuple[str, str]:
    """Return (new_difficulty, adjustment) given the current difficulty and an evaluation's average score."""
    current = DifficultyLevel(current_difficulty)
    adjustment = decide_adjustment(average_score)
    new_level = apply_adjustment(current, adjustment)
    return new_level.value, adjustment.value
