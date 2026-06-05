"""
NEXA HUB — DB Service Layer
db_service.py

All database read/write operations for fitness tracker.
Health service calls these instead of reading JSON files.
"""

import datetime
from django.utils import timezone
from django.db.models import Avg, Sum, Max, Min, Count


# ── Lazy imports to avoid circular deps ───────────────────────
def _models():
    from VoiceAssistant.VoiceAssistant.models import (
        FitnessEntry, WeeklyFitnessLog, GoalTarget, ChatHistory, Reminder
    )
    return FitnessEntry, WeeklyFitnessLog, GoalTarget, ChatHistory, Reminder


# ═════════════════════════════════════════════════════════════
# WRITE: Save user-submitted fitness data
# ═════════════════════════════════════════════════════════════

def save_fitness_entry(session_id: str, data: dict, date=None) -> dict:
    """
    Upsert a FitnessEntry for session_id + date.
    Returns the saved entry as dict.
    """
    FitnessEntry, *_ = _models()
    today = date or timezone.localdate()

    # Build update fields (only non-None values)
    fields = {}
    field_map = {
        'steps':              int,
        'distance_km':        float,
        'sleep_hours':        float,
        'deep_sleep_hours':   float,
        'rem_sleep_hours':    float,
        'bedtime':            str,
        'wake_time':          str,
        'sleep_quality':      str,
        'water_liters':       float,
        'calories_burned':    int,
        'calories_consumed':  int,
        'heart_rate_resting': int,
        'heart_rate_max':     int,
        'heart_rate_avg':     int,
        'weight_kg':          float,
        'height_cm':          float,
        'stress_score':       int,
        'recovery_score':     int,
        'mood':               str,
        'notes':              str,
        'source':             str,
    }
    for key, cast in field_map.items():
        if key in data and data[key] not in (None, '', 'null'):
            try:
                fields[key] = cast(data[key])
            except (ValueError, TypeError):
                pass

    entry, created = FitnessEntry.objects.update_or_create(
        session_id=session_id,
        date=today,
        defaults=fields
    )

    # Auto-compute distance if not provided
    if entry.steps and not entry.distance_km:
        entry.distance_km = round(entry.steps * 0.00076, 2)
        entry.save(update_fields=['distance_km'])

    # Regenerate weekly log
    _refresh_weekly_log(session_id, today)

    return _entry_to_dict(entry)


def set_goal(session_id: str, metric: str, target_value: float) -> dict:
    """Set or update a fitness goal."""
    _, _, GoalTarget, *_ = _models()
    goal, _ = GoalTarget.objects.update_or_create(
        session_id=session_id,
        metric=metric,
        defaults={'target_value': target_value, 'achieved': False}
    )
    return {'metric': goal.metric, 'target': goal.target_value}


def save_chat(session_id: str, role: str, message: str, **kwargs):
    """Log a chat message."""
    _, _, _, ChatHistory, _ = _models()
    ChatHistory.objects.create(
        session_id=session_id, role=role, message=message, **kwargs
    )


# ═════════════════════════════════════════════════════════════
# READ: Fetch user's data for responses
# ═════════════════════════════════════════════════════════════

def get_today(session_id: str) -> dict:
    """Return today's FitnessEntry as dict, or empty dict."""
    FitnessEntry, *_ = _models()
    try:
        entry = FitnessEntry.objects.get(
            session_id=session_id, date=timezone.localdate()
        )
        return _entry_to_dict(entry)
    except FitnessEntry.DoesNotExist:
        return {}


def get_entry_by_date(session_id: str, date) -> dict:
    FitnessEntry, *_ = _models()
    try:
        entry = FitnessEntry.objects.get(session_id=session_id, date=date)
        return _entry_to_dict(entry)
    except FitnessEntry.DoesNotExist:
        return {}


def get_last_n_days(session_id: str, n: int = 7) -> list:
    """Return last n days of entries as list of dicts."""
    FitnessEntry, *_ = _models()
    since = timezone.localdate() - datetime.timedelta(days=n - 1)
    qs = FitnessEntry.objects.filter(
        session_id=session_id,
        date__gte=since,
        date__lte=timezone.localdate()
    ).order_by('date')
    return [_entry_to_dict(e) for e in qs]


def get_weekly_summary(session_id: str, week_offset: int = 0) -> dict:
    """
    Returns aggregated weekly stats.
    week_offset=0 → current week, -1 → last week.
    """
    FitnessEntry, WeeklyFitnessLog, *_ = _models()
    today = timezone.localdate()
    monday = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(weeks=week_offset)
    sunday = monday + datetime.timedelta(days=6)

    entries = FitnessEntry.objects.filter(
        session_id=session_id,
        date__gte=monday,
        date__lte=sunday
    ).order_by('date')

    if not entries.exists():
        return {}

    days_data = {e.date.strftime('%a'): e for e in entries}

    agg = entries.aggregate(
        avg_steps=Avg('steps'),
        total_steps=Sum('steps'),
        avg_sleep=Avg('sleep_hours'),
        avg_water=Avg('water_liters'),
        total_calories=Sum('calories_burned'),
        avg_hr=Avg('heart_rate_avg'),
        avg_recovery=Avg('recovery_score'),
        avg_stress=Avg('stress_score'),
        days=Count('id'),
    )

    # Best day by steps
    best_entry = entries.order_by('-steps').first()
    best_day   = best_entry.date.strftime('%A') if best_entry and best_entry.steps else None

    # Per-day steps for chart
    day_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    steps_by_day = {}
    for i, name in enumerate(day_names):
        d = monday + datetime.timedelta(days=i)
        try:
            e = entries.get(date=d)
            steps_by_day[name] = e.steps or 0
        except FitnessEntry.DoesNotExist:
            steps_by_day[name] = 0

    consistency = round((agg['days'] / 7) * 100, 1)

    return {
        'week':            f"{monday.strftime('%d %b')} – {sunday.strftime('%d %b %Y')}",
        'week_start':      str(monday),
        'week_end':        str(sunday),
        'avg_steps':       round(agg['avg_steps'] or 0),
        'total_steps':     agg['total_steps'] or 0,
        'avg_sleep':       round(agg['avg_sleep'] or 0, 1),
        'avg_water':       round(agg['avg_water'] or 0, 1),
        'total_calories':  agg['total_calories'] or 0,
        'avg_hr':          round(agg['avg_hr'] or 0),
        'avg_recovery':    round(agg['avg_recovery'] or 0, 1),
        'avg_stress':      round(agg['avg_stress'] or 0, 1),
        'consistency':     consistency,
        'days_logged':     agg['days'],
        'best_day':        best_day,
        'steps_by_day':    steps_by_day,
    }


def get_monthly_summary(session_id: str) -> dict:
    """Current month's aggregated stats."""
    FitnessEntry, *_ = _models()
    today   = timezone.localdate()
    month_start = today.replace(day=1)

    entries = FitnessEntry.objects.filter(
        session_id=session_id,
        date__gte=month_start,
        date__lte=today
    )
    if not entries.exists():
        return {}

    agg = entries.aggregate(
        total_steps=Sum('steps'),
        avg_steps=Avg('steps'),
        avg_sleep=Avg('sleep_hours'),
        avg_water=Avg('water_liters'),
        total_calories=Sum('calories_burned'),
        avg_hr=Avg('heart_rate_avg'),
        avg_recovery=Avg('recovery_score'),
        days=Count('id'),
    )

    # Weight change
    first_weight = entries.exclude(weight_kg=None).order_by('date').first()
    last_weight  = entries.exclude(weight_kg=None).order_by('-date').first()
    weight_change = None
    if first_weight and last_weight and first_weight != last_weight:
        weight_change = round((last_weight.weight_kg or 0) - (first_weight.weight_kg or 0), 1)

    # Best week
    best_week_start = None
    best_week_avg   = 0
    for week_offset in range(-4, 1):
        ws = get_weekly_summary(session_id, week_offset)
        if ws.get('avg_steps', 0) > best_week_avg:
            best_week_avg   = ws['avg_steps']
            best_week_start = ws.get('week_start')

    return {
        'month':         today.strftime('%B %Y'),
        'total_steps':   agg['total_steps'] or 0,
        'avg_daily_steps': round(agg['avg_steps'] or 0),
        'avg_sleep':     round(agg['avg_sleep'] or 0, 1),
        'avg_water':     round(agg['avg_water'] or 0, 1),
        'total_calories': agg['total_calories'] or 0,
        'avg_hr':        round(agg['avg_hr'] or 0),
        'avg_recovery':  round(agg['avg_recovery'] or 0, 1),
        'days_logged':   agg['days'],
        'weight_change': weight_change,
        'best_week_start': best_week_start,
        'consistency':   round((agg['days'] / max(today.day, 1)) * 100, 1),
    }


def get_goals(session_id: str) -> dict:
    _, _, GoalTarget, *_ = _models()
    goals = GoalTarget.objects.filter(session_id=session_id)
    return {g.metric: g.target_value for g in goals}


def compare_with_prev(session_id: str, metric: str, days_back: int = 7) -> dict:
    """Compare today vs N days ago for a given metric."""
    FitnessEntry, *_ = _models()
    today     = timezone.localdate()
    prev_date = today - datetime.timedelta(days=days_back)
    try:
        today_val = getattr(FitnessEntry.objects.get(session_id=session_id, date=today), metric)
    except FitnessEntry.DoesNotExist:
        today_val = None
    try:
        prev_val  = getattr(FitnessEntry.objects.get(session_id=session_id, date=prev_date), metric)
    except FitnessEntry.DoesNotExist:
        prev_val  = None

    if today_val is not None and prev_val is not None:
        diff     = today_val - prev_val
        pct      = round((diff / max(abs(prev_val), 1)) * 100, 1)
        trend    = 'up' if diff > 0 else ('down' if diff < 0 else 'same')
    else:
        diff, pct, trend = None, None, 'unknown'

    return {
        'metric':    metric,
        'today':     today_val,
        'previous':  prev_val,
        'diff':      diff,
        'pct_change': pct,
        'trend':     trend,
        'period':    f'last {days_back} days',
    }


def get_chat_history(session_id: str, last_n: int = 20) -> list:
    _, _, _, ChatHistory, _ = _models()
    msgs = ChatHistory.objects.filter(session_id=session_id).order_by('-timestamp')[:last_n]
    return [{'role': m.role, 'message': m.message, 'ts': str(m.timestamp)} for m in reversed(msgs)]


def has_any_data(session_id: str) -> bool:
    FitnessEntry, *_ = _models()
    return FitnessEntry.objects.filter(session_id=session_id).exists()


# ═════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════════════════════

def _entry_to_dict(entry) -> dict:
    """Serialize a FitnessEntry to dict (includes computed fields)."""
    return {
        'date':               str(entry.date),
        'steps':              entry.steps,
        'distance_km':        entry.distance_km,
        'sleep_hours':        entry.sleep_hours,
        'deep_sleep_hours':   entry.deep_sleep_hours,
        'rem_sleep_hours':    entry.rem_sleep_hours,
        'bedtime':            entry.bedtime,
        'wake_time':          entry.wake_time,
        'sleep_quality':      entry.sleep_quality,
        'water_liters':       entry.water_liters,
        'calories_burned':    entry.calories_burned,
        'calories_consumed':  entry.calories_consumed,
        'heart_rate_resting': entry.heart_rate_resting,
        'heart_rate_max':     entry.heart_rate_max,
        'heart_rate_avg':     entry.heart_rate_avg,
        'weight_kg':          entry.weight_kg,
        'height_cm':          entry.height_cm,
        'bmi':                entry.bmi,
        'bmi_category':       entry.bmi_category,
        'stress_score':       entry.stress_score,
        'recovery_score':     entry.recovery_score,
        'mood':               entry.mood,
        'notes':              entry.notes,
        'overall_score':      entry.overall_score,
        'calorie_deficit':    entry.calorie_deficit,
        'source':             entry.source,
    }


def _refresh_weekly_log(session_id: str, date):
    """Recompute and upsert WeeklyFitnessLog for the week containing `date`."""
    FitnessEntry, WeeklyFitnessLog, *_ = _models()
    monday = date - datetime.timedelta(days=date.weekday())
    sunday = monday + datetime.timedelta(days=6)

    entries = FitnessEntry.objects.filter(
        session_id=session_id,
        date__gte=monday,
        date__lte=sunday
    )
    if not entries.exists():
        return

    agg = entries.aggregate(
        avg_steps=Avg('steps'),
        total_steps=Sum('steps'),
        avg_sleep=Avg('sleep_hours'),
        avg_water=Avg('water_liters'),
        total_calories=Sum('calories_burned'),
        avg_hr=Avg('heart_rate_avg'),
        avg_recovery=Avg('recovery_score'),
        avg_stress=Avg('stress_score'),
        days=Count('id'),
    )
    best = entries.order_by('-steps').first()

    WeeklyFitnessLog.objects.update_or_create(
        session_id=session_id,
        week_start=monday,
        defaults={
            'week_end':       sunday,
            'avg_steps':      round(agg['avg_steps'] or 0),
            'total_steps':    agg['total_steps'],
            'avg_sleep':      round(agg['avg_sleep'] or 0, 1) if agg['avg_sleep'] else None,
            'avg_water':      round(agg['avg_water'] or 0, 1) if agg['avg_water'] else None,
            'total_calories': agg['total_calories'],
            'avg_hr':         round(agg['avg_hr']) if agg['avg_hr'] else None,
            'avg_recovery':   round(agg['avg_recovery'] or 0, 1) if agg['avg_recovery'] else None,
            'avg_stress':     round(agg['avg_stress'] or 0, 1) if agg['avg_stress'] else None,
            'consistency_pct': round((agg['days'] / 7) * 100, 1),
            'best_day':       best.date.strftime('%A') if best and best.steps else None,
            'days_logged':    agg['days'],
        }
    )