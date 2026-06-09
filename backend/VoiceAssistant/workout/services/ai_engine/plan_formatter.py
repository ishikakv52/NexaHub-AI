"""
plan_formatter.py
Formats the raw workout list into the final API response structure.
"""
from __future__ import annotations

from ..utils.helpers import format_duration


def format_plan(exercises: list[dict], profile: dict) -> dict:
    """
    Build the complete workout plan response.

    Args:
        exercises: List of prescribed exercise dicts from workout_generator.
        profile: Enriched user profile.

    Returns:
        Complete plan dict ready to serialize to JSON.
    """
    total_calories = _estimate_calories(exercises, profile["available_minutes"])

    return {
        "plan": {
            "summary": _build_summary(profile),
            "profile_insights": _build_insights(profile),
            "exercises": exercises,
            "total_exercises": len(exercises),
            "estimated_duration": format_duration(profile["available_minutes"] * 60),
            "estimated_calories": round(total_calories),
            "intensity_label": profile["intensity"].capitalize(),
            "bmi": profile["bmi"],
            "bmi_category": profile["bmi_category"],
        }
    }


def _build_summary(profile: dict) -> str:
    goal_labels = {
        "lose_weight": "Weight Loss",
        "gain_weight": "Muscle & Weight Gain",
        "maintain_weight": "Maintenance & Fitness",
    }
    activity_labels = {
        "workout": "Strength & Cardio Workout",
        "yoga": "Yoga Flow",
        "stretching": "Stretching Routine",
        "mobility": "Mobility Training",
        "breathing": "Breathing & Mindfulness",
    }
    goal = goal_labels.get(profile["goal"], profile["goal"])
    activity = activity_labels.get(profile["activity_type"], profile["activity_type"])
    level = profile["experience_level"].capitalize()
    minutes = profile["available_minutes"]

    return (
        f"{level} {activity} for {goal} — {minutes} minute session"
    )


def _build_insights(profile: dict) -> list[str]:
    insights = []
    bmi = profile["bmi"]
    goal = profile["goal"]
    intensity = profile["intensity"]

    # BMI insight
    insights.append(
        f"Your BMI is {bmi} ({profile['bmi_category']}). "
        + _bmi_advice(bmi, goal)
    )

    # Intensity insight
    intensity_advice = {
        "low": "We've set a comfortable pace to build your foundation safely.",
        "medium": "Moderate intensity selected to balance challenge and recovery.",
        "high": "High intensity selected to maximize results for your goal.",
    }
    insights.append(intensity_advice.get(intensity, ""))

    return [i for i in insights if i]


def _bmi_advice(bmi: float, goal: str) -> str:
    if bmi < 18.5:
        return "Focus on nutrient-dense meals alongside your training."
    if bmi < 25:
        return "You're in a healthy range — great foundation for any goal."
    if bmi < 30:
        return "Consistent training and mindful eating will support your progress."
    return "Start at a comfortable pace and gradually increase intensity."


def _estimate_calories(exercises: list[dict], total_minutes: int) -> float:
    """Rough MET-based calorie estimate."""
    avg_cal_per_min = (
        sum(e.get("calories_per_minute", 5) for e in exercises) / max(len(exercises), 1)
    )
    return avg_cal_per_min * total_minutes