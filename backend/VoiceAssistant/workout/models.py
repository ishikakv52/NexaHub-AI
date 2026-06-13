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
    LOSE = "lose_weight", "Lose Weight"
    GAIN = "gain_weight", "Gain Weight"
    MAINTAIN = "maintain_weight", "Maintain Weight"


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
        blank=True,
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

    # New field: short form tips shown on the card
    tips = models.TextField(blank=True)

    # New field: whether the exercise is time-based (hold/plank) vs rep-based
    is_timed = models.BooleanField(
        default=False,
        help_text="Check this for time-based exercises (e.g. plank, hold). "
                  "Leave unchecked for rep-based exercises."
    )

    # New field: equipment required (e.g. "Dumbbells", "None", "Resistance Band")
    equipment_needed = models.CharField(
        max_length=100,
        blank=True,
        default="None",
        help_text="Equipment required, e.g. 'Dumbbells', 'Resistance Band', or leave blank for none."
    )

    default_sets = models.IntegerField(default=3)
    default_reps = models.IntegerField(default=12)
    default_duration_seconds = models.IntegerField(default=60)
    default_rest_seconds = models.IntegerField(default=45)

    # Renamed from calories_per_min → calories_per_minute for consistency
    calories_per_minute = models.FloatField(default=5)

    # YouTube URL (full URL, e.g. https://www.youtube.com/watch?v=abc123)
    youtube_url = models.URLField(
        blank=True,
        help_text="Paste the full YouTube URL, e.g. https://www.youtube.com/watch?v=abc123 "
                  "OR the embed URL https://www.youtube.com/embed/abc123. "
                  "The embed URL is auto-generated."
    )
    video_url = models.URLField(
    blank=True,
    null=True,
    help_text="Cloudinary video URL"
    )
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def youtube_embed_url(self) -> str:
        """
        Auto-converts any YouTube URL format into an embed URL.
        Handles:
          - https://www.youtube.com/watch?v=VIDEO_ID
          - https://youtu.be/VIDEO_ID
          - https://www.youtube.com/embed/VIDEO_ID  (already embed)
          - Empty string → returns ""
        """
        url = (self.youtube_url or "").strip()
        if not url:
            return ""

        # Already an embed URL
        if "youtube.com/embed/" in url:
            return url

        # youtu.be short link
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[-1].split("?")[0].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"

        # Standard watch URL
        if "youtube.com/watch" in url:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            video_id_list = params.get("v", [])
            if video_id_list:
                return f"https://www.youtube.com/embed/{video_id_list[0]}"

        # Fallback: return as-is (user may have pasted a non-standard URL)
        return url


# =====================
# MUSCLE GROUP
# =====================

class MuscleGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# =====================
# USER FITNESS PROFILE
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


# =====================
# WORKOUT SESSION
# =====================

class WorkoutSession(models.Model):
    """
    Stores every generated workout plan for analytics and ML training.
    Directly stores the user inputs so we don't need a separate profile
    record for anonymous / guest users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Unique key returned to the frontend so it can submit feedback later
    session_key = models.CharField(max_length=64, unique=True, db_index=True)

    # ── Snapshot of user inputs ──────────────────────────────────────────────
    age = models.PositiveIntegerField()
    weight_kg = models.FloatField()
    height_cm = models.FloatField()
    goal = models.CharField(max_length=30, choices=FitnessGoal.choices)
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    experience_level = models.CharField(max_length=30, choices=DifficultyLevel.choices)
    available_minutes = models.IntegerField()

    # ── Derived values stored for ML feature set ──────────────────────────────
    bmi = models.FloatField(default=0)
    bmi_category = models.CharField(max_length=30, blank=True)

    # ── Generated plan ────────────────────────────────────────────────────────
    plan_json = models.JSONField(default=dict)

    # ── Timestamps ────────────────────────────────────────────────────────────
    started = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(null=True, blank=True)

    # ── Feedback ──────────────────────────────────────────────────────────────
    user_rating = models.IntegerField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Session {self.session_key[:8]}… | {self.activity_type} | {self.goal}"


# =====================
# WORKOUT PLAN (optional/legacy — kept for compatibility)
# =====================

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


class RecommendationLog(models.Model):
    session_id = models.CharField(max_length=150)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    engine_version = models.CharField(max_length=50, default="rule_based_v1")
    created = models.DateTimeField(auto_now_add=True)