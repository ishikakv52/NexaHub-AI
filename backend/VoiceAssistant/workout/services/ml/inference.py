"""
inference.py — ML-based exercise scoring (future integration).
When enabled, replaces or augments the rule-based recommender.
"""
from __future__ import annotations

from pathlib import Path

MODEL_PATH = Path(__file__).parent / "saved_models" / "workout_recommender.pkl"

_model = None  # Lazy-loaded singleton


def load_model():
    global _model
    if _model is None:
        try:
            import joblib
            _model = joblib.load(MODEL_PATH)
        except FileNotFoundError:
            _model = None
    return _model


def ml_score_exercises(exercises: list, profile: dict) -> list:
    """
    Score exercises using ML model and return sorted list.
    Falls back to original order if model not available.

    Args:
        exercises: List of Exercise ORM instances.
        profile: Enriched user profile dict.

    Returns:
        Exercises sorted by predicted user satisfaction score.
    """
    model = load_model()
    if model is None:
        # ML not ready — return as-is (rule engine handles ordering)
        return exercises

    try:
        import numpy as np
        from .preprocess import GOAL_MAP, ACTIVITY_MAP, EXPERIENCE_MAP

        features = np.array([[
            profile["age"],
            profile["weight_kg"],
            profile["height_cm"],
            profile["bmi"],
            GOAL_MAP.get(profile["goal"], 0),
            ACTIVITY_MAP.get(profile["activity_type"], 0),
            EXPERIENCE_MAP.get(profile["experience_level"], 0),
            profile["available_minutes"],
        ]] * len(exercises))

        scores = model.predict_proba(features)[:, -1]  # Probability of highest rating
        sorted_exercises = [
            ex for _, ex in sorted(zip(scores, exercises), key=lambda x: -x[0])
        ]
        return sorted_exercises
    except Exception:
        return exercises


def is_ml_ready() -> bool:
    """Check if a trained ML model is available."""
    return MODEL_PATH.exists()