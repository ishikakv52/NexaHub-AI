"""
workout_generator.py
Takes selected exercises and a user profile and prescribes
sets, reps, duration, and rest for each exercise.
"""
from __future__ import annotations

from ..utils.helpers import clamp, format_duration


# Prescription tables keyed by (intensity, goal)
# Values: (sets, reps_multiplier, rest_seconds_multiplier, duration_multiplier)
PRESCRIPTION_TABLE = {
    ("low",    "lose_weight"):     (3, 0.8, 1.2, 1.0),
    ("low",    "gain_weight"):     (3, 0.8, 1.0, 1.0),
    ("low",    "maintain_weight"): (3, 1.0, 1.0, 1.0),
    ("medium", "lose_weight"):     (4, 1.0, 0.9, 1.1),
    ("medium", "gain_weight"):     (4, 1.2, 1.1, 1.0),
    ("medium", "maintain_weight"): (3, 1.0, 1.0, 1.0),
    ("high",   "lose_weight"):     (5, 1.2, 0.8, 1.3),
    ("high",   "gain_weight"):     (5, 1.4, 1.2, 1.1),
    ("high",   "maintain_weight"): (4, 1.1, 1.0, 1.1),
}


def prescribe_exercise(exercise, profile: dict) -> dict:
    """
    Apply rule-based prescription to a single Exercise instance.
    Returns a dict with all display-ready fields.
    """
    intensity = profile["intensity"]
    goal = profile["goal"]

    key = (intensity, goal)
    sets_count, reps_mult, rest_mult, dur_mult = PRESCRIPTION_TABLE.get(
        key, (3, 1.0, 1.0, 1.0)
    )

    # Sets
    sets = clamp(int(exercise.default_sets * (sets_count / 3)), 1, 8)

    # Reps or Duration
    if exercise.is_timed:
        duration_sec = clamp(
            int(exercise.default_duration_seconds * dur_mult), 10, 300
        )
        reps = 0
        reps_display = "—"
        duration_display = format_duration(duration_sec)
    else:
        reps = clamp(int(exercise.default_reps * reps_mult), 1, 30)
        duration_sec = exercise.default_duration_seconds
        reps_display = str(reps)
        duration_display = format_duration(duration_sec) if duration_sec else "—"

    # Rest
    rest_sec = clamp(int(exercise.default_rest_seconds * rest_mult), 15, 180)
    rest_display = format_duration(rest_sec)

    return {
    "id": exercise.pk,
    "name": exercise.name,
    "activity_type": exercise.get_activity_type_display(),
    "difficulty": str(exercise.difficulty),
    "category": str(exercise.category) if exercise.category else "",
    "sets": sets,
    "reps": reps_display,
    "duration": duration_display,
    "rest_time": rest_display,
    "instructions": exercise.instructions or "",
    "tips": exercise.tips or "",
    "equipment": exercise.equipment_needed or "None",
    "video_url": exercise.video_url or "",
    "calories_per_minute": exercise.calories_per_minute,
}



def generate_workout(exercises: list, profile: dict) -> list[dict]:
    """
    Generate prescription for all selected exercises.
    Returns a list of prescribed exercise dicts.
    """
    return [prescribe_exercise(ex, profile) for ex in exercises]