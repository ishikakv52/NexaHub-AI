from django.contrib import admin
from .models import UserProfile, Food, MealPlan, Meal, WaterLog, ProgressLog, WeightHistory


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'goal', 'daily_calories', 'bmi')
    list_filter = ('goal', 'food_preference', 'activity_level')


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'calories', 'protein', 'diet_type', 'meal_type')
    list_filter = ('category', 'diet_type', 'meal_type')
    search_fields = ('name',)


class MealInline(admin.TabularInline):
    model = Meal
    extra = 0


@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'daily_calories', 'is_active')
    inlines = [MealInline]


@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount_ml', 'date')


@admin.register(ProgressLog)
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'calories_consumed', 'water_consumed_ml')


@admin.register(WeightHistory)
class WeightHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight_kg', 'bmi', 'recorded_at')
