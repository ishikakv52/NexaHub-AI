# Data migration: seeds the default Free and Premium (Monthly) plans,
# and backfills UserSubscription + CreditWallet rows for any existing users
# so the system works immediately for current users without manual steps.

from django.db import migrations


def seed_plans_and_backfill(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    UserSubscription = apps.get_model("subscriptions", "UserSubscription")
    CreditWallet = apps.get_model("subscriptions", "CreditWallet")
    User = apps.get_model(*__import__("django.conf", fromlist=["settings"]).settings.AUTH_USER_MODEL.split("."))

    free_plan, _ = SubscriptionPlan.objects.get_or_create(
        plan_type="free",
        defaults={
            "name": "Free",
            "description": "Default free plan: 2000 credits on day 1, then 1200 credits daily.",
            "price_in_paise": 0,
            "currency": "INR",
            "duration_days": 0,
            "daily_credits": 1200,
            "signup_bonus_credits": 2000,
            "is_unlimited": False,
            "is_active": True,
        },
    )

    SubscriptionPlan.objects.get_or_create(
        plan_type="premium",
        name="Premium Monthly",
        defaults={
            "description": "Unlimited AI feature access for 30 days.",
            "price_in_paise": 19900,  # ₹199 — admin can change in Django Admin
            "currency": "INR",
            "duration_days": 30,
            "daily_credits": 1200,
            "signup_bonus_credits": 2000,
            "is_unlimited": True,
            "is_active": True,
        },
    )

    # Backfill existing users with a Free subscription + full credit wallet.
    # These are EXISTING users (not new signups), so they receive the
    # steady-state daily_credits amount directly and are marked as having
    # already received their signup bonus (no retroactive 2000 bonus).
    from django.utils import timezone

    now = timezone.now()
    for user in User.objects.all():
        UserSubscription.objects.get_or_create(
            user=user,
            defaults={
                "plan": free_plan,
                "status": "active",
                "started_at": now,
                "expires_at": None,
            },
        )
        CreditWallet.objects.get_or_create(
            user=user,
            defaults={
                "balance": free_plan.daily_credits,
                "daily_allowance": free_plan.daily_credits,
                "last_refreshed_at": now,
                "has_received_signup_bonus": True,
            },
        )


def reverse_noop(apps, schema_editor):
    # Intentionally left as a no-op; reversing would delete plan/usage data.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans_and_backfill, reverse_noop),
    ]