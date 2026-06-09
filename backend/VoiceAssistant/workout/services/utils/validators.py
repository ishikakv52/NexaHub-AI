"""
Input validation for user workout parameters.
All validators raise ValueError on invalid input.
"""
from __future__ import annotations


VALID_GOALS = {"lose_weight", "gain_weight", "maintain_weight"}
VALID_ACTIVITY_TYPES = {"workout", "yoga", "stretching", "mobility", "breathing"}
VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced"}


def validate_age(value) -> int:
    try:
        age = int(value)
    except (TypeError, ValueError):
        raise ValueError("Age must be a number.")
    if not (10 <= age <= 100):
        raise ValueError("Age must be between 10 and 100.")
    return age


def validate_weight(value) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        raise ValueError("Weight must be a number.")
    if not (20 <= weight <= 300):
        raise ValueError("Weight must be between 20 kg and 300 kg.")
    return round(weight, 2)


def validate_height(value) -> float:
    try:
        height = float(value)
    except (TypeError, ValueError):
        raise ValueError("Height must be a number.")
    if not (100 <= height <= 250):
        raise ValueError("Height must be between 100 cm and 250 cm.")
    return round(height, 2)


def validate_goal(value: str) -> str:
    val = str(value).lower().strip()
    if val not in VALID_GOALS:
        raise ValueError(f"Goal must be one of: {', '.join(VALID_GOALS)}")
    return val


def validate_activity_type(value: str) -> str:
    val = str(value).lower().strip()
    if val not in VALID_ACTIVITY_TYPES:
        raise ValueError(f"Activity type must be one of: {', '.join(VALID_ACTIVITY_TYPES)}")
    return val


def validate_experience_level(value: str) -> str:
    val = str(value).lower().strip()
    if val not in VALID_EXPERIENCE_LEVELS:
        raise ValueError(
            f"Experience level must be one of: {', '.join(VALID_EXPERIENCE_LEVELS)}"
        )
    return val


def validate_available_minutes(value) -> int:
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        raise ValueError("Available time must be a number.")
    if not (5 <= minutes <= 180):
        raise ValueError("Available time must be between 5 and 180 minutes.")
    return minutes


def validate_user_input(data: dict) -> dict:
    """Validate and sanitize the full user input dict. Returns cleaned dict."""
    return {
        "age": validate_age(data.get("age")),
        "weight_kg": validate_weight(data.get("weight_kg")),
        "height_cm": validate_height(data.get("height_cm")),
        "goal": validate_goal(data.get("goal")),
        "activity_type": validate_activity_type(data.get("activity_type")),
        "experience_level": validate_experience_level(data.get("experience_level")),
        "available_minutes": validate_available_minutes(data.get("available_minutes")),
    }