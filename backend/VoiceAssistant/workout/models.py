from django.db import models
from django.contrib.auth.models import User


# =====================
# ENUMS
# =====================

class ActivityType(models.TextChoices):
    WORKOUT = "workout", "Workout"
    YOGA = "yoga", "Yoga"
    STRETCHING = "stretching", "Stretching"
    MOBILITY = "mobility", "Mobility"
    BREATHING = "breathing", "Breathing"


class DifficultyLevel(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class FitnessGoal(models.TextChoices):
    LOSE = "lose", "Lose Weight"
    GAIN = "gain", "Gain Weight"
    MAINTAIN = "maintain", "Maintain Weight"


# =====================
# CATEGORY
# =====================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =====================
# EXERCISE
# =====================

class Exercise(models.Model):
    name = models.CharField(max_length=150)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="exercises"
    )

    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices
    )

    difficulty = models.CharField(
        max_length=30,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER
    )

    description = models.TextField()
    instructions = models.TextField(blank=True)

    default_sets = models.IntegerField(default=3)
    default_reps = models.IntegerField(default=12)
    default_duration_seconds = models.IntegerField(default=60)
    default_rest_seconds = models.IntegerField(default=45)

    calories_per_min = models.FloatField(default=5)

    youtube_url = models.URLField(blank=True)

    tags = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# =====================
# MUSCLE GROUP
# =====================

class MuscleGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# =====================
# OTHER MODELS (UNCHANGED)
# =====================

class UserFitnessProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=150, blank=True)

    age = models.PositiveIntegerField()
    weight = models.FloatField()
    height = models.FloatField()

    goal = models.CharField(max_length=30, choices=FitnessGoal.choices)
    experience = models.CharField(max_length=30, choices=DifficultyLevel.choices)
    preferred_activity = models.CharField(max_length=30, choices=ActivityType.choices)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def bmi(self):
        h = self.height / 100
        return round(self.weight / (h * h), 1)


class WorkoutPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=150, blank=True)
    profile = models.ForeignKey(UserFitnessProfile, on_delete=models.CASCADE, related_name="plans")

    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    duration_minutes = models.IntegerField()

    generated_plan = models.JSONField(default=dict)
    estimated_calories = models.FloatField(default=0)

    ai_version = models.CharField(max_length=50, default="rule_based_v1")

    created = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)


class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=150, blank=True)
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.SET_NULL, null=True)

    started = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(null=True, blank=True)

    calories_burned = models.FloatField(default=0)
    completed = models.BooleanField(default=False)


class RecommendationLog(models.Model):
    session_id = models.CharField(max_length=150)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    engine_version = models.CharField(max_length=50, default="rule_based_v1")
    created = models.DateTimeField(auto_now_add=True)