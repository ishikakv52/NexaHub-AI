"""
subscriptions/models.py

Models for the Premium Subscription & Daily Credit System.

Design:
    - SubscriptionPlan: configurable plans (Free / Premium / future plans)
    - UserSubscription: tracks each user's current plan, status, and expiry
    - CreditWallet: tracks daily credit balance, refreshed lazily on access
    - CreditUsageLog: audit trail of credit consumption
    - PaymentTransaction: Razorpay order/payment records

All models reference django.contrib.auth.models.User (default user model),
as confirmed from accounts/models.py (no custom User model in this project).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Subscription Plans
# ---------------------------------------------------------------------------
class SubscriptionPlan(models.Model):
    """
    Defines a subscription plan that can be purchased.

    Designed for future expansion — additional plans (e.g. "Pro Yearly",
    "Team Plan") can simply be added as new rows without any code changes,
    as long as they follow the same pricing/duration/credit structure.
    """

    class PlanType(models.TextChoices):
        FREE = "free", "Free"
        PREMIUM = "premium", "Premium"

    name = models.CharField(max_length=100, unique=True)
    plan_type = models.CharField(
        max_length=20, choices=PlanType.choices, default=PlanType.PREMIUM
    )
    description = models.TextField(blank=True)

    # Price in the smallest currency unit (paise for INR), as required by Razorpay.
    price_in_paise = models.PositiveIntegerField(
        default=0,
        help_text="Price in paise (e.g. ₹199 = 19900). Set 0 for free plans.",
    )
    currency = models.CharField(max_length=10, default="INR")

    # Duration of premium access granted by this plan, in days.
    duration_days = models.PositiveIntegerField(
        default=30,
        help_text="Number of days premium access remains active after purchase.",
    )

    # For free plan / fallback — daily credit allowance.
    daily_credits = models.PositiveIntegerField(
        default=1200,
        help_text="Steady-state daily credit allowance (from day 2 onwards).",
    )

    signup_bonus_credits = models.PositiveIntegerField(
        default=2000,
        help_text="One-time credit amount given on the user's first day "
                   "(day of signup). From day 2 onwards, daily_credits applies.",
    )

    # Premium plans grant unlimited usage; this flag drives that behaviour.
    is_unlimited = models.BooleanField(
        default=False,
        help_text="If True, users on this plan bypass all credit checks.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Inactive plans are hidden from purchase but preserved for history.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price_in_paise"]
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} ({self.get_plan_type_display()})"

    @property
    def price_in_rupees(self):
        return self.price_in_paise / 100


# ---------------------------------------------------------------------------
# User Subscription
# ---------------------------------------------------------------------------
class UserSubscription(models.Model):
    """
    Tracks the current subscription state for a user.

    Every user gets exactly one UserSubscription row (created on first access
    via get_or_create). Defaults to the Free plan.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Null/blank means no expiry (e.g. permanent free plan).",
    )

    auto_downgraded = models.BooleanField(
        default=False,
        help_text="Set to True once an expired premium plan has been auto-downgraded.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def __str__(self):
        return f"{self.user.username} -> {self.plan.name} ({self.status})"

    # ------------------------------------------------------------------
    # Business logic helpers
    # ------------------------------------------------------------------
    def is_premium_active(self):
        """
        Returns True if the user currently has active, unexpired premium access.
        """
        if self.plan.plan_type != SubscriptionPlan.PlanType.PREMIUM:
            return False
        if self.status != self.Status.ACTIVE:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True

    def has_expired(self):
        """
        Returns True if this subscription has an expiry date that has passed.
        """
        return bool(self.expires_at and self.expires_at <= timezone.now())

    def downgrade_to_free(self):
        """
        Downgrades this subscription to the default Free plan and marks
        it as expired + auto-downgraded. Idempotent.
        """
        free_plan = SubscriptionPlan.objects.filter(
            plan_type=SubscriptionPlan.PlanType.FREE, is_active=True
        ).first()

        if free_plan is None:
            # Safety fallback: should not happen if data migration ran,
            # but avoids hard failure in production.
            free_plan, _ = SubscriptionPlan.objects.get_or_create(
                plan_type=SubscriptionPlan.PlanType.FREE,
                defaults={
                    "name": "Free",
                    "price_in_paise": 0,
                    "duration_days": 0,
                    "daily_credits": 1200,
                    "signup_bonus_credits": 2000,
                    "is_unlimited": False,
                },
            )

        self.plan = free_plan
        self.status = self.Status.EXPIRED
        self.expires_at = None
        self.auto_downgraded = True
        self.save(update_fields=["plan", "status", "expires_at", "auto_downgraded", "updated_at"])

    def activate_premium(self, plan: SubscriptionPlan):
        """
        Activates a premium plan for this user starting now, setting
        expiry based on the plan's duration_days.
        """
        now = timezone.now()
        self.plan = plan
        self.status = self.Status.ACTIVE
        self.started_at = now
        self.expires_at = now + timezone.timedelta(days=plan.duration_days)
        self.auto_downgraded = False
        self.save(update_fields=[
            "plan", "status", "started_at", "expires_at",
            "auto_downgraded", "updated_at",
        ])

    def ensure_not_expired(self):
        """
        Checks expiry and auto-downgrades if needed. Call this lazily
        before any access check. Returns True if a downgrade occurred.
        """
        if self.plan.plan_type == SubscriptionPlan.PlanType.PREMIUM and self.has_expired():
            self.downgrade_to_free()
            return True
        return False


# ---------------------------------------------------------------------------
# Credit Wallet (daily credits for free users)
# ---------------------------------------------------------------------------
class CreditWallet(models.Model):
    """
    Tracks the daily credit balance for a user.

    Refresh strategy: LAZY. Credits are refreshed to the plan's
    `daily_credits` value the first time the wallet is accessed on a new
    day (compared via `last_refreshed_at.date()` vs `timezone.now().date()`).
    This requires no Celery/cron — see `subscriptions/services.py`.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_wallet",
    )

    balance = models.PositiveIntegerField(default=0)
    daily_allowance = models.PositiveIntegerField(
        default=1500,
        help_text="Snapshot of the plan's daily credit allowance.",
    )

    last_refreshed_at = models.DateTimeField(default=timezone.now)

    has_received_signup_bonus = models.BooleanField(
        default=False,
        help_text="True once the one-time signup bonus has been granted "
                   "(on wallet creation / first refresh).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Credit Wallet"
        verbose_name_plural = "Credit Wallets"

    def __str__(self):
        return f"{self.user.username}: {self.balance}/{self.daily_allowance}"

    def needs_refresh(self):
        """
        True if the wallet hasn't been refreshed today (server local date,
        based on Django's current timezone, i.e. timezone.localtime).
        """
        last_local = timezone.localtime(self.last_refreshed_at).date()
        today_local = timezone.localtime(timezone.now()).date()
        return last_local < today_local

    def refresh_if_needed(self, daily_allowance=None, signup_bonus=None):
        """
        Refreshes the wallet to full balance if a new day has started.

        - If this is the FIRST refresh ever for this wallet AND it hasn't
          received its signup bonus yet, the balance is set to
          `signup_bonus` (Day 1 credits).
        - Otherwise, the balance is set to `daily_allowance` (steady-state
          daily credits, Day 2 onwards).

        Returns True if a refresh occurred.
        """
        if not self.needs_refresh():
            # Keep allowance in sync even without a refresh, in case the
            # user's plan changed (e.g. upgraded mid-day).
            if daily_allowance is not None and self.daily_allowance != daily_allowance:
                self.daily_allowance = daily_allowance
                self.save(update_fields=["daily_allowance", "updated_at"])
            return False

        allowance = daily_allowance if daily_allowance is not None else self.daily_allowance

        if not self.has_received_signup_bonus:
            # Day 1: grant signup bonus instead of the regular daily allowance.
            bonus = signup_bonus if signup_bonus is not None else allowance
            self.balance = bonus
            self.has_received_signup_bonus = True
        else:
            # Day 2+: regular steady-state daily credits.
            self.balance = allowance

        self.daily_allowance = allowance
        self.last_refreshed_at = timezone.now()
        self.save(update_fields=[
            "balance", "daily_allowance", "last_refreshed_at",
            "has_received_signup_bonus", "updated_at",
        ])
        return True

    def has_sufficient_credits(self, amount=1):
        return self.balance >= amount

    def deduct(self, amount=1):
        """
        Deducts `amount` credits. Raises ValueError if insufficient.
        Caller is responsible for calling refresh_if_needed() first.
        """
        if self.balance < amount:
            raise ValueError("Insufficient credits")
        self.balance = models.F("balance") - amount
        self.save(update_fields=["balance", "updated_at"])
        self.refresh_from_db(fields=["balance"])


# ---------------------------------------------------------------------------
# Credit Usage Log (audit trail)
# ---------------------------------------------------------------------------
class CreditUsageLog(models.Model):
    """
    Records each credit deduction event for auditing/analytics.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_usage_logs",
    )
    amount = models.PositiveIntegerField(default=1)
    feature = models.CharField(
        max_length=100,
        help_text="Identifier for the feature/endpoint that consumed credits, "
                   "e.g. 'remedies.ai_chat', 'workout.generate_plan'.",
    )
    balance_after = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Credit Usage Log"
        verbose_name_plural = "Credit Usage Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} used {self.amount} on {self.feature} @ {self.created_at}"


# ---------------------------------------------------------------------------
# Payment Transactions (Razorpay)
# ---------------------------------------------------------------------------
class PaymentTransaction(models.Model):
    """
    Stores Razorpay order/payment lifecycle data for auditing and
    reconciliation. Created when an order is initiated, updated on
    webhook/verification callback.
    """

    class Status(models.TextChoices):
        CREATED = "created", "Order Created"
        PAID = "paid", "Paid / Verified"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="payment_transactions",
    )

    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    amount_in_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="INR")

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED
    )

    failure_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.razorpay_order_id} ({self.status})"

    def mark_paid(self, payment_id, signature):
        self.razorpay_payment_id = payment_id
        self.razorpay_signature = signature
        self.status = self.Status.PAID
        self.save(update_fields=["razorpay_payment_id", "razorpay_signature", "status", "updated_at"])

    def mark_failed(self, reason=""):
        self.status = self.Status.FAILED
        self.failure_reason = reason
        self.save(update_fields=["status", "failure_reason", "updated_at"])