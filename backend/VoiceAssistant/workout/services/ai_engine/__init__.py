"""
AI Engine package — Workout system
Exports all core AI/rule engine functions in one place.
"""

from .prompt_builder import build_user_profile

from .recommender import select_exercises

from .workout_generator import generate_workout

from .plan_formatter import format_plan