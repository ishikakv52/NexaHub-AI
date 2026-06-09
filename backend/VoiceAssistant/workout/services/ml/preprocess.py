"""
preprocess.py — ML data preprocessing (future integration).
Converts WorkoutSession records into feature vectors for training.
"""
from __future__ import annotations

import json
from pathlib import Path


FEATURE_COLUMNS = [
    "age",
    "weight_kg",
    "height_cm",
    "bmi",
    "goal_encoded",
    "activity_type_encoded",
    "experience_encoded",
    "available_minutes",
]

GOAL_MAP = {"lose_weight": 0, "gain_weight": 1, "maintain_weight": 2}
ACTIVITY_MAP = {
    "workout": 0,
    "yoga": 1,
    "stretching": 2,
    "mobility": 3,
    "breathing": 4,
}
EXPERIENCE_MAP = {"beginner": 0, "intermediate": 1, "advanced": 2}


def session_to_features(session) -> dict:
    """
    Convert a WorkoutSession ORM object to a flat feature dict.
    """
    return {
        "age": session.age,
        "weight_kg": session.weight_kg,
        "height_cm": session.height_cm,
        "bmi": session.bmi,
        "goal_encoded": GOAL_MAP.get(session.goal, -1),
        "activity_type_encoded": ACTIVITY_MAP.get(session.activity_type, -1),
        "experience_encoded": EXPERIENCE_MAP.get(session.experience_level, -1),
        "available_minutes": session.available_minutes,
        # Target (for supervised learning)
        "user_rating": session.user_rating,
        "completed": int(session.completed) if session.completed is not None else None,
    }


def export_dataset(output_path: str = "datasets/workout_logs.json"):
    """
    Export all rated WorkoutSessions to JSON for ML training.
    Run via: python manage.py shell -c "from workout.services.ml.preprocess import export_dataset; export_dataset()"
    """
    # Import here to avoid circular imports at module load
    from workout.models import WorkoutSession  # noqa

    sessions = WorkoutSession.objects.filter(user_rating__isnull=False)
    records = [session_to_features(s) for s in sessions]

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Exported {len(records)} records to {path}")
    return records