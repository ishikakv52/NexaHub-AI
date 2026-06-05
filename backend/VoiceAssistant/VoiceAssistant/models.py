"""
NEXA HUB — Database Models (Full)
FitnessEntry: user ka daily fitness data (DB-backed)
ChatHistory:  conversation log
WeeklyLog:    auto-aggregated weekly summary
GoalTarget:   user-set fitness goals
"""

from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


# ───────────────────────────────────────────────────────────────
# 1. DAILY FITNESS ENTRY  (main table — ek row = ek din ka data)
# ───────────────────────────────────────────────────────────────
class FitnessEntry(models.Model):
    """
    Stores ONE day's complete fitness data per session/user.
    session_id = anonymous identifier stored in browser localStorage.
    user       = if logged-in user links their account.
    """

    # ── Identity ────────────────────────────────────────────────
    session_id = models.CharField(
        max_length=128, db_index=True,
        help_text="Browser session ID (localStorage)"
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fitness_entries'
    )
    date = models.DateField(default=timezone.localdate, db_index=True)

    # ── Steps & Movement ────────────────────────────────────────
    steps       = models.IntegerField(null=True, blank=True, help_text="Steps today")
    distance_km = models.FloatField(null=True,  blank=True, help_text="km walked/run")

    # ── Sleep ───────────────────────────────────────────────────
    sleep_hours      = models.FloatField(null=True, blank=True, help_text="Total sleep hrs")
    deep_sleep_hours = models.FloatField(null=True, blank=True, help_text="Deep sleep hrs")
    rem_sleep_hours  = models.FloatField(null=True, blank=True, help_text="REM sleep hrs")
    bedtime          = models.CharField(max_length=16, null=True, blank=True)
    wake_time        = models.CharField(max_length=16, null=True, blank=True)
    sleep_quality    = models.CharField(
        max_length=16, null=True, blank=True,
        choices=[('Poor','Poor'),('Fair','Fair'),('Good','Good'),('Excellent','Excellent')]
    )

    # ── Water ───────────────────────────────────────────────────
    water_liters = models.FloatField(null=True, blank=True, help_text="Litres consumed")

    # ── Calories ────────────────────────────────────────────────
    calories_burned   = models.IntegerField(null=True, blank=True)
    calories_consumed = models.IntegerField(null=True, blank=True)

    # ── Heart Rate ──────────────────────────────────────────────
    heart_rate_resting = models.IntegerField(null=True, blank=True, help_text="BPM resting")
    heart_rate_max     = models.IntegerField(null=True, blank=True, help_text="BPM max today")
    heart_rate_avg     = models.IntegerField(null=True, blank=True)

    # ── Body Metrics ────────────────────────────────────────────
    weight_kg = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True, help_text="Set once, reused")

    # ── Wellness ────────────────────────────────────────────────
    stress_score   = models.IntegerField(null=True, blank=True, help_text="0–100")
    recovery_score = models.IntegerField(null=True, blank=True, help_text="0–100")
    mood           = models.CharField(
        max_length=16, null=True, blank=True,
        choices=[('Great','Great'),('Good','Good'),('Neutral','Neutral'),('Low','Low'),('Terrible','Terrible')]
    )

    # ── Meta ────────────────────────────────────────────────────
    notes      = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source     = models.CharField(
        max_length=32, default='manual',
        choices=[('manual','Manual Input'),('voice','Voice Input'),('auto','Auto/Computed')]
    )

    class Meta:
        unique_together = ('session_id', 'date')
        ordering = ['-date']
        verbose_name = 'Fitness Entry'
        verbose_name_plural = 'Fitness Entries'
        indexes = [
            models.Index(fields=['session_id', 'date']),
        ]

    def __str__(self):
        return f"[{self.date}] session={self.session_id[:8]}… steps={self.steps} sleep={self.sleep_hours}h"

    @property
    def bmi(self):
        if self.weight_kg and self.height_cm and self.height_cm > 0:
            h = self.height_cm / 100
            return round(self.weight_kg / (h * h), 1)
        return None

    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi is None:
            return None
        if bmi < 18.5: return 'Underweight'
        if bmi < 25:   return 'Normal'
        if bmi < 30:   return 'Overweight'
        return 'Obese'

    @property
    def calorie_deficit(self):
        if self.calories_consumed and self.calories_burned:
            return self.calories_consumed - self.calories_burned
        return None

    @property
    def overall_score(self):
        """0–100 composite health score for the day."""
        scores, weights = [], []
        if self.steps is not None:
            scores.append(min(self.steps / 10000, 1) * 100)
            weights.append(0.25)
        if self.sleep_hours is not None:
            scores.append(min(self.sleep_hours / 8, 1) * 100)
            weights.append(0.25)
        if self.water_liters is not None:
            scores.append(min(self.water_liters / 3, 1) * 100)
            weights.append(0.20)
        if self.recovery_score is not None:
            scores.append(self.recovery_score)
            weights.append(0.30)
        if not scores:
            return 0
        total_w = sum(weights)
        return round(sum(s * w for s, w in zip(scores, weights)) / total_w, 1)


# ───────────────────────────────────────────────────────────────
# 2. WEEKLY FITNESS LOG  (auto-aggregated)
# ───────────────────────────────────────────────────────────────
class WeeklyFitnessLog(models.Model):
    session_id     = models.CharField(max_length=128, db_index=True)
    week_start     = models.DateField(db_index=True)    # Monday of that week
    week_end       = models.DateField()                 # Sunday

    avg_steps      = models.IntegerField(null=True, blank=True)
    total_steps    = models.IntegerField(null=True, blank=True)
    avg_sleep      = models.FloatField(null=True, blank=True)
    avg_water      = models.FloatField(null=True, blank=True)
    total_calories = models.IntegerField(null=True, blank=True)
    avg_hr         = models.IntegerField(null=True, blank=True)
    avg_recovery   = models.FloatField(null=True, blank=True)
    avg_stress     = models.FloatField(null=True, blank=True)
    consistency_pct= models.FloatField(null=True, blank=True,
                        help_text="% of days with ≥1 entry")
    best_day       = models.CharField(max_length=16, null=True, blank=True)
    days_logged    = models.IntegerField(default=0)
    computed_at    = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('session_id', 'week_start')
        ordering = ['-week_start']

    def __str__(self):
        return f"Week {self.week_start} → {self.week_end} [{self.session_id[:8]}]"


# ───────────────────────────────────────────────────────────────
# 3. GOAL TARGET  (user-set goals per metric)
# ───────────────────────────────────────────────────────────────
class GoalTarget(models.Model):
    METRIC_CHOICES = [
        ('steps',        'Daily Steps'),
        ('sleep_hours',  'Sleep Hours'),
        ('water_liters', 'Water (L)'),
        ('weight_kg',    'Weight (kg)'),
        ('calories_burned', 'Calories Burned'),
        ('recovery_score',  'Recovery Score'),
    ]

    session_id   = models.CharField(max_length=128, db_index=True)
    user         = models.ForeignKey(User, on_delete=models.SET_NULL,
                     null=True, blank=True)
    metric       = models.CharField(max_length=32, choices=METRIC_CHOICES)
    target_value = models.FloatField()
    set_on       = models.DateField(auto_now_add=True)
    achieved     = models.BooleanField(default=False)
    achieved_on  = models.DateField(null=True, blank=True)
    notes        = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('session_id', 'metric')

    def __str__(self):
        return f"{self.metric}={self.target_value} [{self.session_id[:8]}]"


# ───────────────────────────────────────────────────────────────
# 4. CHAT HISTORY  (complete conversation log)
# ───────────────────────────────────────────────────────────────
class ChatHistory(models.Model):
    ROLE_CHOICES = [('user','User'),('ai','AI')]

    session_id    = models.CharField(max_length=128, db_index=True)
    role          = models.CharField(max_length=8, choices=ROLE_CHOICES)
    message       = models.TextField()
    model         = models.CharField(max_length=64, null=True, blank=True)
    sub_model     = models.CharField(max_length=64, null=True, blank=True)
    intent        = models.CharField(max_length=128, null=True, blank=True)
    report_type   = models.CharField(max_length=64,  null=True, blank=True)
    report_data   = models.JSONField(null=True, blank=True)
    timestamp     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes  = [models.Index(fields=['session_id', 'timestamp'])]

    def __str__(self):
        return f"[{self.role}] {self.message[:60]}"


# ───────────────────────────────────────────────────────────────
# 5. REMINDER  (user-set smart reminders)
# ───────────────────────────────────────────────────────────────
class Reminder(models.Model):
    session_id  = models.CharField(max_length=128, db_index=True)
    title       = models.CharField(max_length=255)
    remind_time = models.TimeField()
    active      = models.BooleanField(default=True)
    repeat      = models.CharField(
        max_length=16, default='daily',
        choices=[('daily','Daily'),('weekdays','Weekdays'),('once','Once')]
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} @ {self.remind_time} [{self.session_id[:8]}]"


# ── Keep existing models from original codebase ────────────────
class UserProfile(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=64, default='UTC')
    preferred_language = models.CharField(max_length=8, default='en')
    phone    = models.CharField(max_length=32, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} profile"


class Conversation(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                    null=True, blank=True)
    session_id = models.CharField(max_length=128, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_active= models.DateTimeField(auto_now=True)
    context    = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Conversation {self.session_id} ({self.user or 'anon'})"


class IntentLog(models.Model):
    user        = models.ForeignKey(User, on_delete=models.SET_NULL,
                    null=True, blank=True)
    session     = models.ForeignKey(Conversation, on_delete=models.SET_NULL,
                    null=True, blank=True)
    intent      = models.CharField(max_length=128)
    utterance   = models.TextField()
    detected_at = models.DateTimeField(auto_now_add=True)
    confidence  = models.FloatField(null=True, blank=True)
    resolved    = models.BooleanField(default=False)
    response    = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.intent} @ {self.detected_at}"


class HealthGoal(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE,
                     null=True, blank=True)
    name         = models.CharField(max_length=128)
    target_value = models.FloatField(null=True, blank=True)
    unit         = models.CharField(max_length=32, default='units')
    start_date   = models.DateField(null=True, blank=True)
    end_date     = models.DateField(null=True, blank=True)
    progress     = models.FloatField(default=0.0)
    active       = models.BooleanField(default=True)
    metadata     = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.user or 'anon'})"


class Task(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                   null=True, blank=True)
    title      = models.CharField(max_length=255)
    done       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date   = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({'done' if self.done else 'pending'})"