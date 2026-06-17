import json
import datetime
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .calculations import compute_profile_metrics, get_bmi_category, get_goal_progress_with_history
from .forms import SignUpForm, UserProfileForm, WeightUpdateForm
from .meal_engine import generate_meal_plan, get_meals_grouped, get_day_totals, generate_grocery_list, MEAL_TYPES
from .models import UserProfile, Food, MealPlan, Meal, WaterLog, ProgressLog, WeightHistory


from django.shortcuts import render, redirect, get_object_or_404
def index(request):
    return render(request, 'index.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Let\'s set up your profile.')
            return redirect('profile')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


def _update_progress_log(user, date, meal_plan):
    """Recalculate and save today's consumed nutrition from all consumed meals."""
    consumed_meals = Meal.objects.filter(
        meal_plan=meal_plan,
        is_consumed=True,
    )
    # For the dashboard we track the day's consumed meals
    # We map meal_plan day -> calendar date
    # meal_plan.start_date may be a date or a datetime; normalize to date
    start_date = meal_plan.start_date.date() if isinstance(meal_plan.start_date, datetime.datetime) else meal_plan.start_date
    day_offset = (date - start_date).days % 7
    day_num = day_offset + 1
    day_meals = consumed_meals.filter(day=day_num)

    totals = day_meals.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbs'),
        fat=Sum('fat'),
    )

    water_total = WaterLog.objects.filter(user=user, date=date).aggregate(
        total=Sum('amount_ml')
    )['total'] or 0

    progress_log, _ = ProgressLog.objects.get_or_create(user=user, date=date)
    progress_log.calories_consumed = totals['calories'] or 0
    progress_log.protein_consumed = totals['protein'] or 0
    progress_log.carbs_consumed = totals['carbs'] or 0
    progress_log.fat_consumed = totals['fat'] or 0
    progress_log.water_consumed_ml = water_total
    progress_log.save()
    return progress_log


@login_required
def dashboard(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile:
        return redirect('profile')

    today = timezone.now().date()
    meal_plan = MealPlan.objects.filter(user=request.user, is_active=True).first()
    day_num = 1

    today_meals = {}
    today_totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    consumed_totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}

    if meal_plan:
        start_date = meal_plan.start_date.date() if isinstance(meal_plan.start_date, datetime.datetime) else meal_plan.start_date
        day_offset = (today - start_date).days % 7
        day_num = day_offset + 1
        grouped = get_meals_grouped(meal_plan)
        today_meals = grouped.get(day_num, {})
        today_totals = get_day_totals(today_meals)

        # Consumed totals (only eaten meals)
        for meal in today_meals.values():
            if meal.is_consumed:
                consumed_totals['calories'] += meal.calories
                consumed_totals['protein'] += meal.protein
                consumed_totals['carbs'] += meal.carbs
                consumed_totals['fat'] += meal.fat
        consumed_totals = {k: round(v, 1) for k, v in consumed_totals.items()}

        # Keep progress log in sync
        _update_progress_log(request.user, today, meal_plan)

        # Build ordered list of today's meals for UI (breakfast -> dinner)
        today_meals_list = []
        for mt in MEAL_TYPES:
            if mt in today_meals:
                today_meals_list.append(today_meals[mt])
        
        # Meals eaten summary
        meals_total = len(today_meals_list)
        meals_eaten = sum(1 for m in today_meals_list if m.is_consumed)
        meals_eaten_percent = int(round((meals_eaten / meals_total) * 100)) if meals_total else 0
    water_today = WaterLog.objects.filter(user=request.user, date=today).aggregate(
        total=Sum('amount_ml')
    )['total'] or 0

    bmi_label, bmi_class = get_bmi_category(profile.bmi)

    weight_history_qs = WeightHistory.objects.filter(user=request.user)
    goal_progress = get_goal_progress_with_history(
        weight_history_qs, profile.weight_kg, profile.target_weight_kg, profile.goal
    )

    # Get chart data for graphs
    weight_history_for_chart = WeightHistory.objects.filter(user=request.user).order_by('recorded_at')[:30]
    week_start = today - timedelta(days=6)
    weekly_logs = ProgressLog.objects.filter(user=request.user, date__gte=week_start).order_by('date')
    
    weight_data = [{'date': w.recorded_at.strftime('%b %d'), 'weight': w.weight_kg, 'bmi': w.bmi} for w in weight_history_for_chart]
    calorie_data = [{'date': p.date.strftime('%b %d'), 'calories': p.calories_consumed} for p in weekly_logs]

    calorie_goal = profile.daily_calories or 1
    protein_goal = profile.daily_protein or 1
    carbs_goal = round(profile.daily_calories * 0.45 / 4, 1) or 1
    fat_goal = round(profile.daily_calories * 0.25 / 9, 1) or 1
    water_goal = profile.daily_water_ml or 2000

    context = {
        'profile': profile,
        'meal_plan': meal_plan,
        'today_meals': today_meals,
        'today_totals': today_totals,
        'consumed_totals': consumed_totals,
        'water_today': water_today,
        'water_goal': water_goal,
        'water_percent': min(round((water_today / water_goal) * 100, 1), 100),
        'calorie_goal': calorie_goal,
        'protein_goal': protein_goal,
        'carbs_goal': carbs_goal,
        'fat_goal': fat_goal,
        'bmi_label': bmi_label,
        'bmi_class': bmi_class,
        'goal_progress': goal_progress,
        'day_num': day_num,
        # Safe percent values for progress bars (never divide by zero)
        'cal_percent': min(round((consumed_totals['calories'] / calorie_goal) * 100, 1), 100),
        'protein_percent': min(round((consumed_totals['protein'] / protein_goal) * 100, 1), 100),
        'carbs_percent': min(round((consumed_totals['carbs'] / carbs_goal) * 100, 1), 100),
        'fat_percent': min(round((consumed_totals['fat'] / fat_goal) * 100, 1), 100),
        'meal_types': MEAL_TYPES,
        'today_meals_list': today_meals_list,
        'today': today,
        'meals_total': meals_total,
        'meals_eaten': meals_eaten,
        'meals_eaten_percent': meals_eaten_percent,
        'weight_data_json': json.dumps(weight_data),
        'calorie_data_json': json.dumps(calorie_data),
    }
    return render(request, 'dashboard.html', context)


@login_required
def profile_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            metrics = compute_profile_metrics(profile)
            for key, val in metrics.items():
                setattr(profile, key, val)
            profile.save()

            WeightHistory.objects.create(
                user=request.user,
                weight_kg=profile.weight_kg,
                bmi=profile.bmi,
            )

            generate_meal_plan(request.user, profile)
            messages.success(request, 'Profile saved! Your personalized diet plan has been generated.')
            return redirect('dashboard')
    else:
        initial = {'full_name': request.user.get_full_name() or request.user.username}
        form = UserProfileForm(instance=profile, initial=initial if not profile else None)

    return render(request, 'profile.html', {'form': form, 'profile': profile})


@login_required
def diet_plan_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile:
        return redirect('profile')

    meal_plan = MealPlan.objects.filter(user=request.user, is_active=True).first()
    if not meal_plan:
        meal_plan = generate_meal_plan(request.user, profile)

    if request.method == 'POST' and 'regenerate' in request.POST:
        meal_plan = generate_meal_plan(request.user, profile)
        messages.success(request, 'Your diet plan has been regenerated!')

    grouped = get_meals_grouped(meal_plan)
    meal_type_labels = {
        'breakfast': 'Breakfast',
        'morning_snack': 'Morning Snack',
        'lunch': 'Lunch',
        'evening_snack': 'Evening Snack',
        'dinner': 'Dinner',
    }
    meal_type_icons = {
        'breakfast': 'bi-sunrise',
        'morning_snack': 'bi-cup-hot',
        'lunch': 'bi-sun',
        'evening_snack': 'bi-cookie',
        'dinner': 'bi-moon-stars',
    }

    today = timezone.now().date()
    # Normalize meal_plan.start_date to date if it is a datetime
    start_date = meal_plan.start_date.date() if isinstance(meal_plan.start_date, datetime.datetime) else meal_plan.start_date
    day_offset = (today - start_date).days % 7
    current_day = day_offset + 1

    days_data = []
    for day_num in sorted(grouped.keys()):
        meals = grouped[day_num]
        totals = get_day_totals(meals)
        day_meals = []
        for mt in MEAL_TYPES:
            if mt in meals:
                m = meals[mt]
                day_meals.append({
                    'type': mt,
                    'label': meal_type_labels[mt],
                    'icon': meal_type_icons[mt],
                    'meal': m,
                })
        days_data.append({'day': day_num, 'meals': day_meals, 'totals': totals, 'is_today': day_num == current_day})

    context = {
        'meal_plan': meal_plan,
        'days_data': days_data,
        'profile': profile,
        'current_day': current_day,
    }
    return render(request, 'diet_plan.html', context)


@login_required
def food_library_view(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    diet = request.GET.get('diet', '')

    foods = Food.objects.all()
    if query:
        foods = foods.filter(Q(name__icontains=query))
    if category:
        foods = foods.filter(category=category)
    if diet:
        foods = foods.filter(diet_type=diet)

    categories = Food.CATEGORY_CHOICES
    diet_choices = Food.DIET_CHOICES
    return render(request, 'food_library.html', {
        'foods': foods,
        'categories': categories,
        'diet_choices': diet_choices,
        'query': query,
        'selected_category': category,
        'selected_diet': diet,
        'food_count': foods.count(),
    })


@login_required
def grocery_list_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile:
        return redirect('profile')

    meal_plan = MealPlan.objects.filter(user=request.user, is_active=True).first()
    if not meal_plan:
        meal_plan = generate_meal_plan(request.user, profile)

    grocery = generate_grocery_list(meal_plan)
    total_items = sum(len(g['items']) for g in grocery)
    return render(request, 'grocery_list.html', {
        'grocery': grocery,
        'meal_plan': meal_plan,
        'total_items': total_items,
    })


@login_required
def progress_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile:
        return redirect('profile')

    weight_history = WeightHistory.objects.filter(user=request.user).order_by('recorded_at')[:30]
    progress_logs = ProgressLog.objects.filter(user=request.user).order_by('-date')[:30]

    today = timezone.now().date()
    week_start = today - timedelta(days=6)
    weekly_logs = ProgressLog.objects.filter(user=request.user, date__gte=week_start).order_by('date')

    weight_data = [{'date': w.recorded_at.strftime('%b %d'), 'weight': w.weight_kg, 'bmi': w.bmi} for w in weight_history]
    calorie_data = [{'date': p.date.strftime('%b %d'), 'calories': p.calories_consumed} for p in weekly_logs]
    
    # Macronutrients data for this week
    macros_data = {
        'protein': sum(p.protein_consumed for p in weekly_logs),
        'carbs': sum(p.carbs_consumed for p in weekly_logs),
        'fat': sum(p.fat_consumed for p in weekly_logs),
    }
    
    # Water intake data
    water_data = [{'date': p.date.strftime('%b %d'), 'water': p.water_consumed_ml} for p in weekly_logs]

    if request.method == 'POST':
        form = WeightUpdateForm(request.POST)
        if form.is_valid():
            new_weight = form.cleaned_data['weight_kg']
            profile.weight_kg = new_weight
            metrics = compute_profile_metrics(profile)
            for key, val in metrics.items():
                setattr(profile, key, val)
            profile.save()
            WeightHistory.objects.create(
                user=request.user,
                weight_kg=new_weight,
                bmi=profile.bmi,
            )
            messages.success(request, f'Weight updated to {new_weight} kg!')
            return redirect('progress')
    else:
        form = WeightUpdateForm(initial={'weight_kg': profile.weight_kg})

    weight_history_qs = WeightHistory.objects.filter(user=request.user)
    goal_progress = get_goal_progress_with_history(
        weight_history_qs, profile.weight_kg, profile.target_weight_kg, profile.goal
    )

    # Streak: consecutive days with a progress log
    streak = 0
    check_date = today
    while True:
        if ProgressLog.objects.filter(user=request.user, date=check_date).exists():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    context = {
        'profile': profile,
        'weight_history': weight_history,
        'progress_logs': progress_logs,
        'weight_data_json': json.dumps(weight_data),
        'calorie_data_json': json.dumps(calorie_data),
        'macros_data_json': json.dumps(macros_data),
        'water_data_json': json.dumps(water_data),
        'form': form,
        'goal_progress': goal_progress,
        'streak': streak,
        'total_logs': progress_logs.count(),
    }
    return render(request, 'progress.html', context)


@login_required
@require_POST
def toggle_meal_completion(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id, meal_plan__user=request.user)
    meal.is_consumed = not meal.is_consumed
    meal.save()

    # Update progress log
    today = timezone.now().date()
    meal_plan = meal.meal_plan
    if meal_plan.is_active:
        _update_progress_log(request.user, today, meal_plan)

    # AJAX support
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_consumed': meal.is_consumed,
            'meal_id': meal_id,
        })

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
@require_POST
def add_water(request):
    amount_str = request.POST.get('amount', '250')
    try:
        amount = int(amount_str)
        if amount <= 0 or amount > 5000:
            raise ValueError
    except ValueError:
        amount = 250

    today = timezone.now().date()
    WaterLog.objects.create(
        user=request.user,
        amount_ml=amount,
        date=today,
    )

    # Update progress log water field
    meal_plan = MealPlan.objects.filter(user=request.user, is_active=True).first()
    if meal_plan:
        _update_progress_log(request.user, today, meal_plan)

    # AJAX support
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        water_today = WaterLog.objects.filter(user=request.user, date=today).aggregate(
            total=Sum('amount_ml')
        )['total'] or 0
        profile = UserProfile.objects.filter(user=request.user).first()
        water_goal = profile.daily_water_ml if profile else 2000
        water_percent = min(round((water_today / water_goal) * 100, 1), 100) if water_goal else 0
        return JsonResponse({
            'success': True,
            'water_today': water_today,
            'water_percent': water_percent,
            'amount_added': amount,
        })

    messages.success(request, f'Added {amount}ml of water! 💧')
    return redirect('dashboard')