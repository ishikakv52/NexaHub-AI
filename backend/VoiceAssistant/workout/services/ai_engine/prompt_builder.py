"""
prompt_builder.py
Builds a structured user profile used internally by the rule-based engine
and in future as LLM prompt context.
"""
from __future__ import annotations

from ..utils.helpers import calculate_bmi, bmi_category


def build_user_profile(cleaned_input: dict) -> dict:
    """
    Build an enriched user profile from validated input.
    This acts as the 'prompt context' for the AI engine.
    """
    bmi = calculate_bmi(cleaned_input["weight_kg"], cleaned_input["height_cm"])
    bmi_cat = bmi_category(bmi)

    profile = {
        **cleaned_input,
        "bmi": bmi,
        "bmi_category": bmi_cat,
        # Fitness intensity multiplier (used by rule engine)
        "intensity": _resolve_intensity(
            cleaned_input["experience_level"],
            cleaned_input["goal"],
            bmi,
        ),
        # Target exercise count based on time budget
        "target_exercise_count": _estimate_exercise_count(
            cleaned_input["available_minutes"],
            cleaned_input["activity_type"],
        ),
    }
    return profile


def _resolve_intensity(experience: str, goal: str, bmi: float) -> str:
    """
    Returns 'low', 'medium', or 'high' intensity label.
    Used by the rule engine to select exercise prescriptions.
    """
    if experience == "beginner":
        return "low"
    if experience == "advanced":
        # High BMI + lose weight → high intensity
        if goal == "lose_weight" and bmi >= 25:
            return "high"
        return "high"
    # intermediate
    if goal == "lose_weight":
        return "medium" if bmi < 30 else "high"
    return "medium"


def _estimate_exercise_count(minutes: int, activity_type: str) -> int:
    """
    Estimate how many exercises can fit given the time.
    Different activity types have different average exercise durations.
    """
    avg_minutes = {
        "workout": 5,
        "yoga": 6,
        "stretching": 3,
        "mobility": 4,
        "breathing": 4,
    }
    avg = avg_minutes.get(activity_type, 5)
    count = minutes // avg
    # Clamp to reasonable range
    return max(3, min(count, 12))