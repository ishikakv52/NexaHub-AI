import random
from collections import defaultdict

from .models import Food, Meal, MealPlan

MEAL_TYPES = ['breakfast', 'morning_snack', 'lunch', 'evening_snack', 'dinner']

MEAL_CALORIE_SPLIT = {
    'breakfast': 0.25,
    'morning_snack': 0.10,
    'lunch': 0.30,
    'evening_snack': 0.10,
    'dinner': 0.25,
}

PROTEIN_FOCUS_GOALS = {'weight_loss', 'muscle_gain'}


def _diet_filter(preference):
    if preference == 'vegetarian':
        return ['vegetarian', 'vegan', 'all']
    if preference == 'vegan':
        return ['vegan', 'all']
    return ['non_vegetarian', 'vegetarian', 'vegan', 'all']


def _style_filter(foods, food_style):
    if food_style == 'non_oily':
        return foods.filter(preparation_style__in=['raw', 'boiled', 'steamed', 'grilled', 'baked', 'poached'])
    return foods


def _get_foods_for_meal(preference, food_style, meal_type):
    allowed = _diet_filter(preference)
    foods = Food.objects.filter(diet_type__in=allowed)
    foods = _style_filter(foods, food_style)
    meal_foods = foods.filter(meal_type__in=[meal_type, 'any'])
    if meal_foods.count() < 5:
        meal_foods = _style_filter(Food.objects.filter(diet_type__in=allowed), food_style)
        if meal_foods.count() < 5:
            meal_foods = Food.objects.filter(diet_type__in=allowed)
    return list(meal_foods)


def _pick_food(candidates, used_today, used_week, meal_type, goal):
    random.shuffle(candidates)
    scored = []
    for food in candidates:
        if food.id in used_today:
            continue
        penalty = 0
        if food.id in used_week:
            penalty += 3
        if goal in PROTEIN_FOCUS_GOALS and food.protein >= 8:
            penalty -= 2
        if food.meal_type == meal_type:
            penalty -= 1
        scored.append((penalty, food))
    if not scored:
        return random.choice(candidates) if candidates else None
    scored.sort(key=lambda x: x[0])
    top = scored[:min(5, len(scored))]
    return random.choice(top)[1]


def _calculate_quantity(food, target_calories):
    if food.calories <= 0:
        return food.serving_size_g
    grams = (target_calories / food.calories) * 100
    grams = max(50, min(grams, 350))
    return round(grams / 10) * 10


def generate_meal_plan(user, profile):
    MealPlan.objects.filter(user=user, is_active=True).update(is_active=False)

    meal_plan = MealPlan.objects.create(
        user=user,
        daily_calories=profile.daily_calories,
        daily_protein=profile.daily_protein,
        is_active=True,
    )

    used_week = defaultdict(set)
    all_meals = []

    for day in range(1, 8):
        used_today = set()
        for meal_type in MEAL_TYPES:
            target_cal = profile.daily_calories * MEAL_CALORIE_SPLIT[meal_type]
            candidates = _get_foods_for_meal(profile.food_preference, profile.food_style, meal_type)
            food = _pick_food(candidates, used_today, used_week[meal_type], meal_type, profile.goal)
            if not food:
                continue

            quantity = _calculate_quantity(food, target_cal)
            nutrition = food.nutrition_for_serving(quantity)

            meal = Meal(
                meal_plan=meal_plan,
                day=day,
                meal_type=meal_type,
                food=food,
                quantity_g=quantity,
                calories=nutrition['calories'],
                protein=nutrition['protein'],
                carbs=nutrition['carbs'],
                fat=nutrition['fat'],
            )
            all_meals.append(meal)
            used_today.add(food.id)
            used_week[meal_type].add(food.id)

    Meal.objects.bulk_create(all_meals)
    return meal_plan


def get_meals_grouped(meal_plan):
    grouped = {}
    for meal in meal_plan.meals.select_related('food').all():
        if meal.day not in grouped:
            grouped[meal.day] = {}
        grouped[meal.day][meal.meal_type] = meal
    return grouped


def get_day_totals(meals_for_day):
    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    for meal in meals_for_day.values():
        totals['calories'] += meal.calories
        totals['protein'] += meal.protein
        totals['carbs'] += meal.carbs
        totals['fat'] += meal.fat
    return {k: round(v, 1) for k, v in totals.items()}


def generate_grocery_list(meal_plan):
    items = defaultdict(lambda: {'quantity_g': 0, 'food': None})
    for meal in meal_plan.meals.select_related('food').all():
        key = meal.food.id
        items[key]['quantity_g'] += meal.quantity_g
        items[key]['food'] = meal.food

    grouped = defaultdict(list)
    for data in items.values():
        food = data['food']
        grouped[food.category].append({
            'name': food.name,
            'quantity_g': round(data['quantity_g']),
            'category': food.get_category_display(),
        })

    category_order = ['fruits', 'vegetables', 'dairy', 'protein', 'grains', 'legumes', 'nuts', 'snacks', 'beverages']
    result = []
    for cat in category_order:
        if cat in grouped:
            result.append({
                'category': dict(Food.CATEGORY_CHOICES).get(cat, cat.title()),
                'items': sorted(grouped[cat], key=lambda x: x['name']),
            })
    return result
