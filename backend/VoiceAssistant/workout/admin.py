from django.contrib import admin
from .models import Category, Exercise, MuscleGroup, WorkoutSession


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "activity_type", "is_active")
    list_filter = ("activity_type", "is_active")
    search_fields = ("name",)


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "activity_type", "difficulty", "is_timed", "equipment_needed", "is_active")
    list_filter = ("activity_type", "difficulty", "is_timed", "is_active")
    search_fields = ("name", "description", "tags")

    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "category", "activity_type", "difficulty", "is_active")
        }),
        ("Content", {
            "fields": ("description", "instructions", "tips")
        }),
        ("Prescriptions", {
            "fields": (
                "is_timed",
                "default_sets", "default_reps",
                "default_duration_seconds", "default_rest_seconds",
                "calories_per_minute",
            )
        }),
        ("Equipment & Media", {
            "fields": ("equipment_needed", "youtube_url", "video_url"),
            "description": (
                "Paste any YouTube URL format — watch URL or embed URL. "
                "The embed URL is auto-generated and used on the workout page."
            ),
        }),
        ("Tags", {
            "fields": ("tags",),
            "classes": ("collapse",),
        }),
    )


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_key_short", "activity_type", "goal",
        "experience_level", "available_minutes",
        "bmi", "user_rating", "completed", "started",
    )
    list_filter = ("activity_type", "goal", "experience_level", "completed")
    search_fields = ("session_key",)
    readonly_fields = (
        "session_key", "age", "weight_kg", "height_cm",
        "goal", "activity_type", "experience_level", "available_minutes",
        "bmi", "bmi_category", "plan_json", "started",
    )

    def session_key_short(self, obj):
        return obj.session_key[:12] + "…"
    session_key_short.short_description = "Session"

    def has_add_permission(self, request):
        return False