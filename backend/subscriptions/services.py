"""
subscriptions/services.py

Core business logic for the Premium Subscription & Daily Credit System.

This module is the single source of truth for:
    - Getting/creating a user's subscription + wallet
    - Lazy daily credit refresh
    - Premium expiry detection + auto-downgrade
    - Credit consumption (deduction + logging)
    - Access-check helper used by the decorator

Keeping this logic centralized means views/decorators stay thin and
the same logic can be reused across apps (remedies, workout, etc.)
"""

from django.db import transaction

from .models import (
    CreditUsageLog,
    CreditWallet,
    SubscriptionPlan,
    UserSubscription,
)


DEFAULT_FREE_PLAN_NAME = "Free"


def get_or_create_free_plan():
    """
    Returns the default Free plan, creating it if it doesn't exist.
    Used as a fallback during onboarding and data migrations.
    """
    plan, _ = SubscriptionPlan.objects.get_or_create(
        plan_type=SubscriptionPlan.PlanType.FREE,
        defaults={
            "name": DEFAULT_FREE_PLAN_NAME,
            "description": "Default free plan: 2000 credits on day 1, "
                           "then 1200 credits daily.",
            "price_in_paise": 0,
            "duration_days": 0,
            "daily_credits": 1200,
            "signup_bonus_credits": 2000,
            "is_unlimited": False,
            "is_active": True,
        },
    )
    return plan


@transaction.atomic
def get_or_create_subscription(user):
    """
    Returns the UserSubscription for `user`, creating a default
    Free subscription if one doesn't exist yet.
    """
    try:
        return user.subscription
    except UserSubscription.DoesNotExist:
        free_plan = get_or_create_free_plan()
        return UserSubscription.objects.create(user=user, plan=free_plan)


@transaction.atomic
def get_or_create_wallet(user, daily_allowance=None, signup_bonus=None):
    """
    Returns the CreditWallet for `user`, creating one if needed.

    On creation, the wallet starts with `signup_bonus` credits
    (Day 1 allowance) and is marked has_received_signup_bonus=True,
    so the very next lazy refresh (Day 2) drops to `daily_allowance`.
    """
    try:
        wallet = user.credit_wallet
    except CreditWallet.DoesNotExist:
        allowance = daily_allowance if daily_allowance is not None else 1200
        bonus = signup_bonus if signup_bonus is not None else 2000
        wallet = CreditWallet.objects.create(
            user=user,
            balance=bonus,
            daily_allowance=allowance,
            has_received_signup_bonus=True,
        )
    return wallet


def sync_user_state(user):
    """
    Performs all lazy-sync operations for a user on each access:
        1. Ensures subscription + wallet exist.
        2. Checks for premium expiry -> auto-downgrades if needed.
        3. Refreshes daily credits if a new day has started.

    Returns (subscription, wallet) tuple, both up to date.

    This should be called at the start of any request that needs to
    check access/credits (typically via the decorator).
    """
    subscription = get_or_create_subscription(user)

    # Step 1: handle premium expiry -> auto-downgrade to free.
    subscription.ensure_not_expired()

    # Step 2: ensure wallet exists, synced with current plan's allowance.
    wallet = get_or_create_wallet(
        user,
        daily_allowance=subscription.plan.daily_credits,
        signup_bonus=subscription.plan.signup_bonus_credits,
    )

    # Step 3: lazy daily refresh (only matters for free-plan users,
    # but harmless to call for premium users too).
    wallet.refresh_if_needed(
        daily_allowance=subscription.plan.daily_credits,
        signup_bonus=subscription.plan.signup_bonus_credits,
    )

    return subscription, wallet


class InsufficientCreditsError(Exception):
    """Raised when a user has no remaining credits for a feature."""
    pass


@transaction.atomic
def check_and_consume_credit(user, feature: str, amount: int = 1):
    """
    Main entry point used by the @require_credits decorator.

    1. Syncs subscription/wallet state (expiry + daily refresh).
    2. If user is on an unlimited (premium) plan -> allow, no deduction.
    3. Otherwise, checks balance; if sufficient, deducts and logs usage.
    4. Raises InsufficientCreditsError if balance is too low.

    Returns the (subscription, wallet) tuple for use by the caller
    (e.g. to include remaining credits in the response).
    """
    subscription, wallet = sync_user_state(user)

    if subscription.plan.is_unlimited and subscription.is_premium_active():
        # Premium users: no credit deduction at all.
        return subscription, wallet

    if not wallet.has_sufficient_credits(amount):
        raise InsufficientCreditsError(
            "Daily credit limit reached. Credits will refresh tomorrow "
            "or upgrade to Premium for unlimited access."
        )

    wallet.deduct(amount)
    CreditUsageLog.objects.create(
        user=user,
        amount=amount,
        feature=feature,
        balance_after=wallet.balance,
    )

    return subscription, wallet


def get_subscription_status(user):
    """
    Returns a dict summarizing the user's current subscription + credit
    state. Used by status/profile API endpoints.
    """
    subscription, wallet = sync_user_state(user)

    return {
        "plan_name": subscription.plan.name,
        "plan_type": subscription.plan.plan_type,
        "is_premium": subscription.is_premium_active(),
        "is_unlimited": subscription.plan.is_unlimited and subscription.is_premium_active(),
        "status": subscription.status,
        "started_at": subscription.started_at,
        "expires_at": subscription.expires_at,
        "credits_remaining": wallet.balance,
        "daily_allowance": wallet.daily_allowance,
        "credits_last_refreshed_at": wallet.last_refreshed_at,
    }