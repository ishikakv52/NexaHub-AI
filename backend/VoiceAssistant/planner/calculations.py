ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'lightly_active': 1.375,
    'moderately_active': 1.55,
    'very_active': 1.725,
}

GOAL_CALORIE_ADJUSTMENTS = {
    'weight_loss': -500,
    'weight_gain': 300,
    'muscle_gain': 200,
    'maintain': 0,
}

PROTEIN_MULTIPLIERS = {
    'weight_loss': 1.8,
    'weight_gain': 1.4,
    'muscle_gain': 2.0,
    'maintain': 1.2,
}


def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m ** 2), 1)


def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 1)


def calculate_tdee(bmr, activity_level):
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 1)


def calculate_daily_calories(tdee, goal):
    adjustment = GOAL_CALORIE_ADJUSTMENTS.get(goal, 0)
    calories = tdee + adjustment
    return round(max(calories, 1200), 1)


def calculate_daily_protein(weight_kg, goal):
    multiplier = PROTEIN_MULTIPLIERS.get(goal, 1.2)
    return round(weight_kg * multiplier, 1)


def calculate_daily_water(weight_kg):
    return round(weight_kg * 35, 0)


def get_bmi_category(bmi):
    if bmi < 18.5:
        return 'Underweight', 'warning'
    elif bmi < 25:
        return 'Normal', 'success'
    elif bmi < 30:
        return 'Overweight', 'warning'
    return 'Obese', 'danger'


def get_goal_progress(current_weight, target_weight, goal):
    """
    Returns 0-100 percent progress toward the user's goal.
    For weight_loss / weight_gain we need a reference starting point.
    Since we only have current and target, we compute how far from target
    the user is as a fraction of the gap they need to cover.
    We use the first WeightHistory entry as the starting point when available;
    here we just return how close current is to target relative to a ±10 kg window.
    """
    if goal == 'maintain':
        # Within 1 kg of target = 100%
        diff = abs(current_weight - target_weight)
        return round(max(0, 100 - (diff * 10)), 1)

    if current_weight == target_weight:
        return 100.0

    if goal == 'weight_loss':
        # Progress increases as current_weight decreases toward target
        if current_weight <= target_weight:
            return 100.0
        # We assume the user started at current_weight when they set the profile
        # The denominator is how much they need to lose total (start - target).
        # Without a stored start weight, treat start as current + distance_remaining
        # but clamp meaningfully. Use target difference as the total span.
        # A simpler useful metric: % of target weight achieved
        # e.g. current=80, target=70 -> 0%. current=75, target=70 -> 50%
        # We need WeightHistory for real tracking; for now use profile start assumption.
        # Return inverse of how far from target (as % of target gap from an assumed +10kg start)
        assumed_start = target_weight + max(current_weight - target_weight, 1)
        total = assumed_start - target_weight
        lost = assumed_start - current_weight
        return round(min(max((lost / total) * 100, 0), 100), 1)
    else:
        # weight_gain or muscle_gain
        if current_weight >= target_weight:
            return 100.0
        assumed_start = target_weight - max(target_weight - current_weight, 1)
        total = target_weight - assumed_start
        gained = current_weight - assumed_start
        return round(min(max((gained / total) * 100, 0), 100), 1)


def get_goal_progress_with_history(weight_history_qs, current_weight, target_weight, goal):
    """
    More accurate version that uses the earliest WeightHistory record as start.
    """
    if goal == 'maintain':
        diff = abs(current_weight - target_weight)
        return round(max(0, 100 - (diff * 10)), 1)

    if current_weight == target_weight:
        return 100.0

    earliest = weight_history_qs.order_by('recorded_at').first()
    start_weight = earliest.weight_kg if earliest else current_weight

    if goal == 'weight_loss':
        if current_weight <= target_weight:
            return 100.0
        total = start_weight - target_weight
        if total <= 0:
            return 0.0
        achieved = start_weight - current_weight
        return round(min(max((achieved / total) * 100, 0), 100), 1)
    else:
        if current_weight >= target_weight:
            return 100.0
        total = target_weight - start_weight
        if total <= 0:
            return 0.0
        achieved = current_weight - start_weight
        return round(min(max((achieved / total) * 100, 0), 100), 1)


def compute_profile_metrics(profile):
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
    tdee = calculate_tdee(bmr, profile.activity_level)
    daily_calories = calculate_daily_calories(tdee, profile.goal)
    daily_protein = calculate_daily_protein(profile.weight_kg, profile.goal)
    daily_water = calculate_daily_water(profile.weight_kg)
    return {
        'bmi': bmi,
        'bmr': bmr,
        'tdee': tdee,
        'daily_calories': daily_calories,
        'daily_protein': daily_protein,
        'daily_water_ml': daily_water,
    }