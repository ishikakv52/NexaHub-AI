import random

def select_exercises(profile: dict, queryset) -> list:
    """
    Select exercises from queryset using rule-based filtering.
    """

    activity_type = profile.get("activity_type")
    experience = profile.get("experience_level", "beginner")
    count = profile.get("target_exercise_count", 5)

    qs = queryset

    # basic filters
    qs = qs.filter(is_active=True)

    if activity_type:
        qs = qs.filter(activity_type=activity_type)

    difficulty_map = {
        "beginner": ["beginner"],
        "intermediate": ["beginner", "intermediate"],
        "advanced": ["beginner", "intermediate", "advanced"],
    }

    allowed_difficulties = difficulty_map.get(experience, ["beginner"])

    qs = qs.filter(difficulty__in=allowed_difficulties)

    exercises = list(qs.select_related("category"))

    # fallback
    if not exercises:
        exercises = list(
            queryset.filter(is_active=True).select_related("category")
        )

    random.shuffle(exercises)

    return exercises[:count]