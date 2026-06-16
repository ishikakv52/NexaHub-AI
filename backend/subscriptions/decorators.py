"""
subscriptions/decorators.py

Decorator(s) for gating AI-powered features behind the credit/subscription
system.

Usage example (in any app's views.py):

    from subscriptions.decorators import require_credits

    @require_credits(feature="remedies.ai_chat", amount=1)
    def ai_chat(request):
        ...

Works with both:
    - Plain Django views (request.user)
    - DRF views (request.user via JWTAuthentication, already configured
      in REST_FRAMEWORK settings)

If the user is on an active, unlimited premium plan, the wrapped view
runs normally with no deduction. If on the free plan, 1 (or `amount`)
credit(s) are deducted per call. If credits are exhausted, returns
HTTP 402 Payment Required with a JSON error body.
"""

import functools
import logging

from django.http import JsonResponse

from .services import InsufficientCreditsError, check_and_consume_credit, sync_user_state

logger = logging.getLogger(__name__)


def _authenticate_via_jwt(request):
    """
    Attempts to resolve request.user via JWT, for plain Django views
    (function-based views with @csrf_exempt) that don't go through
    DRF's authentication pipeline.

    Returns the authenticated User object, or None if no valid token
    is present / token is invalid / user is anonymous.

    This is intentionally lenient: any failure returns None rather than
    raising, so callers can decide how to handle missing auth.
    """
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
    except ImportError:
        return None

    try:
        jwt_auth = JWTAuthentication()
        header = jwt_auth.get_header(request)
        if header is None:
            return None
        raw_token = jwt_auth.get_raw_token(header)
        if raw_token is None:
            return None
        validated_token = jwt_auth.get_validated_token(raw_token)
        user = jwt_auth.get_user(validated_token)
        return user
    except Exception:
        return None


def require_credits(feature: str, amount: int = 1):
    """
    View decorator that enforces the credit/subscription system.

    Args:
        feature: A string identifier for analytics/audit
                 (e.g. "remedies.ai_chat").
        amount:  Number of credits this feature call costs (default 1).
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user = getattr(request, "user", None)

            if user is None or not user.is_authenticated:
                return JsonResponse(
                    {"detail": "Authentication required."},
                    status=401,
                )

            try:
                subscription, wallet = check_and_consume_credit(
                    user=user, feature=feature, amount=amount
                )
            except InsufficientCreditsError as exc:
                return JsonResponse(
                    {
                        "detail": str(exc),
                        "error": "insufficient_credits",
                        "credits_remaining": 0,
                        "plan": "free",
                    },
                    status=402,  # Payment Required
                )

            # Attach useful info to the request for the view to optionally use.
            request.subscription = subscription
            request.credit_wallet = wallet

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def attach_subscription_info(view_func):
    """
    Lightweight decorator that syncs + attaches subscription/wallet info
    to the request WITHOUT consuming any credits. Useful for views that
    need to display status but shouldn't charge credits (e.g. dashboards).
    """

    @functools.wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            subscription, wallet = sync_user_state(user)
            request.subscription = subscription
            request.credit_wallet = wallet
        return view_func(request, *args, **kwargs)

    return wrapped_view


def require_credits_fbv(feature: str, amount: int = 1):
    """
    Credit-gating decorator for PLAIN Django function-based views
    (e.g. @csrf_exempt views in remedies, workout, VoiceAssistant,
    VoiceToText, ImageToText, TextToSpeech apps) that do NOT go through
    DRF's authentication pipeline.

    Behaviour:
        - Attempts to resolve request.user via JWT (Authorization: Bearer <token>).
        - If a valid authenticated user is found:
            * Premium (unlimited) users -> pass through, no deduction.
            * Free users -> deduct `amount` credits; if insufficient,
              return HTTP 402 with a JSON error body.
        - If NO valid user is found (anonymous / no token):
            * SAFE FALLBACK: the view runs normally with NO credit
              deduction and NO blocking. This preserves existing
              behaviour for endpoints that aren't yet behind auth,
              so nothing breaks.
            * A debug-level log is emitted so you can audit which
              endpoints are being hit anonymously, and later decide
              whether to require auth here.

    To make this STRICT (block anonymous users entirely once your
    frontend sends JWT to these endpoints), change the `user is None`
    branch below to return a 401 JsonResponse instead of calling
    view_func directly.
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if user is None or not getattr(user, "is_authenticated", False):
                user = _authenticate_via_jwt(request)

            if user is None or not getattr(user, "is_authenticated", False):
                # SAFE FALLBACK — anonymous access, no credit system applied.
                logger.debug(
                    "require_credits_fbv: anonymous access to feature='%s' "
                    "(no valid JWT found) — passing through without credit check.",
                    feature,
                )
                return view_func(request, *args, **kwargs)

            try:
                subscription, wallet = check_and_consume_credit(
                    user=user, feature=feature, amount=amount
                )
            except InsufficientCreditsError as exc:
                return JsonResponse(
                    {
                        "detail": str(exc),
                        "error": "insufficient_credits",
                        "credits_remaining": 0,
                        "plan": "free",
                    },
                    status=402,
                )

            request.user = user
            request.subscription = subscription
            request.credit_wallet = wallet

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator