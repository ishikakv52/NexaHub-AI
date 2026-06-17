from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('lightly_active', 'Lightly Active'),
        ('moderately_active', 'Moderately Active'),
        ('very_active', 'Very Active'),
    ]
    GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('weight_gain', 'Weight Gain'),
        ('muscle_gain', 'Muscle Gain'),
        ('maintain', 'Maintain Weight'),
    ]
    FOOD_PREF_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('non_vegetarian', 'Non Vegetarian'),
        ('vegan', 'Vegan'),
    ]
    FOOD_STYLE_CHOICES = [
        ('simple', 'Simple'),
        ('non_oily', 'Non-Oily'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    height_cm = models.FloatField(help_text='Height in centimeters')
    weight_kg = models.FloatField(help_text='Current weight in kg')
    target_weight_kg = models.FloatField(help_text='Target weight in kg')
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    food_preference = models.CharField(max_length=20, choices=FOOD_PREF_CHOICES)
    food_style = models.CharField(max_length=20, choices=FOOD_STYLE_CHOICES, default='simple')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    bmi = models.FloatField(default=0)
    bmr = models.FloatField(default=0)
    tdee = models.FloatField(default=0)
    daily_calories = models.FloatField(default=0)
    daily_protein = models.FloatField(default=0)
    daily_water_ml = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name}'s Profile"


class Food(models.Model):
    CATEGORY_CHOICES = [
        ('fruits', 'Fruits'),
        ('vegetables', 'Vegetables'),
        ('dairy', 'Dairy'),
        ('protein', 'Protein Sources'),
        ('grains', 'Grains'),
        ('snacks', 'Snacks'),
        ('beverages', 'Beverages'),
        ('nuts', 'Nuts & Seeds'),
        ('legumes', 'Legumes'),
    ]
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('morning_snack', 'Morning Snack'),
        ('lunch', 'Lunch'),
        ('evening_snack', 'Evening Snack'),
        ('dinner', 'Dinner'),
        ('any', 'Any'),
    ]
    DIET_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('non_vegetarian', 'Non Vegetarian'),
        ('vegan', 'Vegan'),
        ('all', 'All'),
    ]
    PREP_STYLE_CHOICES = [
        ('regular', 'Regular'),
        ('raw', 'Raw'),
        ('boiled', 'Boiled'),
        ('steamed', 'Steamed'),
        ('grilled', 'Grilled'),
        ('baked', 'Baked'),
        ('poached', 'Poached'),
    ]

    name = models.CharField(max_length=100)
    calories = models.FloatField(help_text='Per 100g serving')
    protein = models.FloatField(help_text='Grams per 100g')
    carbs = models.FloatField(help_text='Grams per 100g')
    fat = models.FloatField(help_text='Grams per 100g')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, default='any')
    diet_type = models.CharField(max_length=20, choices=DIET_CHOICES, default='all')
    preparation_style = models.CharField(max_length=20, choices=PREP_STYLE_CHOICES, default='regular')
    serving_size_g = models.FloatField(default=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def nutrition_for_serving(self, grams=None):
        g = grams or self.serving_size_g
        factor = g / 100
        return {
            'calories': round(self.calories * factor, 1),
            'protein': round(self.protein * factor, 1),
            'carbs': round(self.carbs * factor, 1),
            'fat': round(self.fat * factor, 1),
        }


class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    start_date = models.DateField(default=timezone.now)
    daily_calories = models.FloatField()
    daily_protein = models.FloatField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Meal Plan for {self.user.username} - {self.start_date}"


class Meal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('morning_snack', 'Morning Snack'),
        ('lunch', 'Lunch'),
        ('evening_snack', 'Evening Snack'),
        ('dinner', 'Dinner'),
    ]
    DAY_CHOICES = [(i, f'Day {i}') for i in range(1, 8)]

    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='meals')
    day = models.PositiveIntegerField(choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity_g = models.FloatField(default=100)
    calories = models.FloatField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fat = models.FloatField()
    is_consumed = models.BooleanField(default=False)

    class Meta:
        ordering = ['day', 'meal_type']

    def __str__(self):
        return f"Day {self.day} - {self.get_meal_type_display()}: {self.food.name}"


class WaterLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_logs')
    amount_ml = models.PositiveIntegerField(default=250)
    logged_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.user.username} - {self.amount_ml}ml on {self.date}"


class ProgressLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_logs')
    date = models.DateField(default=timezone.now)
    calories_consumed = models.FloatField(default=0)
    protein_consumed = models.FloatField(default=0)
    carbs_consumed = models.FloatField(default=0)
    fat_consumed = models.FloatField(default=0)
    water_consumed_ml = models.FloatField(default=0)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class WeightHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_history')
    weight_kg = models.FloatField()
    bmi = models.FloatField()
    recorded_at = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name_plural = 'Weight histories'

    def __str__(self):
        return f"{self.user.username} - {self.weight_kg}kg on {self.recorded_at}"
