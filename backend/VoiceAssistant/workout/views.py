"""
views.py — Workout app API + template view.
"""
import json
import uuid

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Exercise, WorkoutSession
from .services.ai_engine import (
    build_user_profile,
    format_plan,
    generate_workout,
    select_exercises,
)
from .services.ml.inference import ml_score_exercises, is_ml_ready
from .services.utils.validators import validate_user_input


def workout_home(request):
    """Serve the single-page frontend."""
    return render(request, "workout/workout.html")


@csrf_exempt
@require_POST
def generate_plan(request):
    """
    POST /workout/api/generate/
    Body: JSON with user parameters.
    Returns: personalized workout plan JSON.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, Exception):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    # Validate input
    try:
        cleaned = validate_user_input(body)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=422)

    # Build enriched profile
    profile = build_user_profile(cleaned)

    # Fetch exercise queryset
    all_exercises = Exercise.objects.filter(is_active=True).select_related("category")

    # Rule-based selection
    selected = select_exercises(profile, all_exercises)

    # ML re-ranking if model is available
    if is_ml_ready():
        selected = ml_score_exercises(selected, profile)

    if not selected:
        return JsonResponse(
            {
                "error": (
                    "No exercises found for your selection. "
                    "Please ask the admin to add exercises for this activity type."
                )
            },
            status=404,
        )

    # Generate prescriptions
    prescribed = generate_workout(selected, profile)

    # Format complete plan
    result = format_plan(prescribed, profile)

    # Persist session for analytics / future ML training
    session_key = str(uuid.uuid4().hex)
    ws = WorkoutSession.objects.create(
        age=cleaned["age"],
        weight_kg=cleaned["weight_kg"],
        height_cm=cleaned["height_cm"],
        goal=cleaned["goal"],
        activity_type=cleaned["activity_type"],
        experience_level=cleaned["experience_level"],
        available_minutes=cleaned["available_minutes"],
        bmi=profile["bmi"],
        bmi_category=profile["bmi_category"],
        plan_json=result,
        session_key=session_key,
    )
    result["session_key"] = session_key
    result["session_id"] = ws.pk

    return JsonResponse(result, status=200)


@csrf_exempt
@require_POST
def submit_feedback(request):
    """
    POST /workout/api/feedback/
    Body: { session_key, rating (1-5), completed (bool) }
    Stores user feedback for ML training data.
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    session_key = body.get("session_key", "").strip()
    rating = body.get("rating")
    completed = body.get("completed")

    if not session_key:
        return JsonResponse({"error": "session_key is required."}, status=400)

    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({"error": "Rating must be an integer between 1 and 5."}, status=422)

    try:
        session = WorkoutSession.objects.get(session_key=session_key)
    except WorkoutSession.DoesNotExist:
        return JsonResponse({"error": "Session not found."}, status=404)

    session.user_rating = rating
    if completed is not None:
        session.completed = bool(completed)
    session.save(update_fields=["user_rating", "completed"])

    return JsonResponse({"success": True, "message": "Feedback recorded. Thank you!"})


@require_GET
def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse(
        {
            "status": "ok",
            "ml_ready": is_ml_ready(),
            "exercise_count": Exercise.objects.filter(is_active=True).count(),
        }
    )