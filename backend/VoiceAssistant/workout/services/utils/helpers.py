"""
General helper utilities shared across services.
"""
from __future__ import annotations

import math


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal weight"
    if bmi < 30.0:
        return "Overweight"
    return "Obese"


def seconds_to_display(seconds: int) -> str:
    """Convert seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if secs:
        return f"{minutes}m {secs}s"
    return f"{minutes}m"


def distribute_exercises(total_minutes: int, num_exercises: int) -> list[int]:
    """
    Distribute available minutes across exercises.
    Returns a list of per-exercise time budgets in seconds.
    """
    total_seconds = total_minutes * 60
    base = total_seconds // max(num_exercises, 1)
    remainder = total_seconds % max(num_exercises, 1)
    budgets = [base] * num_exercises
    for i in range(remainder):
        budgets[i] += 1
    return budgets


def clamp(value: int | float, min_val: int | float, max_val: int | float):
    return max(min_val, min(max_val, value))


def format_duration(seconds: int) -> str:
    """Returns duration string like '30 seconds' or '2 minutes'."""
    if seconds == 0:
        return "—"
    if seconds < 60:
        return f"{seconds} seconds"
    mins = seconds // 60
    secs = seconds % 60
    if secs:
        return f"{mins} min {secs} sec"
    return f"{mins} min"