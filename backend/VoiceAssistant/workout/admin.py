from django.contrib import admin
from .models import Category, Exercise, MuscleGroup, WorkoutSession


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "activity_type", "is_active")


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "activity_type", "difficulty", "is_active")
    list_filter = ("activity_type", "difficulty", "is_active")
    search_fields = ("name",)


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "completed", "started")
    readonly_fields = [f.name for f in WorkoutSession._meta.fields]

    def has_add_permission(self, request):
        return False