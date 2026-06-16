from django.contrib import admin

# Register your models here.
"""
subscriptions/admin.py

Django Admin configuration for the subscription/credit system.

Provides admin management for:
    - Subscription Plans (create/edit pricing, durations, credit limits)
    - User Subscriptions (view/manage each user's plan, status, expiry)
    - Credit Wallets (view/adjust balances)
    - Credit Usage Logs (read-only audit trail)
    - Payment Transactions (view Razorpay payment records)
"""

from django.contrib import admin

from .models import (
    CreditUsageLog,
    CreditWallet,
    PaymentTransaction,
    SubscriptionPlan,
    UserSubscription,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "plan_type",
        "price_in_rupees_display",
        "duration_days",
        "daily_credits",
        "is_unlimited",
        "is_active",
    )
    list_filter = ("plan_type", "is_active", "is_unlimited")
    search_fields = ("name",)
    ordering = ("price_in_paise",)

    @admin.display(description="Price (₹)")
    def price_in_rupees_display(self, obj):
        return f"₹{obj.price_in_rupees:.2f}"


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "status",
        "is_premium_active_display",
        "started_at",
        "expires_at",
        "auto_downgraded",
    )
    list_filter = ("status", "plan__plan_type", "auto_downgraded")
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user", "plan")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Premium Active?", boolean=True)
    def is_premium_active_display(self, obj):
        return obj.is_premium_active()

    actions = ["downgrade_selected_to_free"]

    @admin.action(description="Downgrade selected users to Free plan")
    def downgrade_selected_to_free(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.downgrade_to_free()
            count += 1
        self.message_user(request, f"{count} subscription(s) downgraded to Free.")


@admin.register(CreditWallet)
class CreditWalletAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "balance",
        "daily_allowance",
        "last_refreshed_at",
        "needs_refresh_display",
    )
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Needs Refresh?", boolean=True)
    def needs_refresh_display(self, obj):
        return obj.needs_refresh()

    actions = ["force_refresh_selected"]

    @admin.action(description="Force refresh selected wallets to full balance")
    def force_refresh_selected(self, request, queryset):
        count = 0
        for wallet in queryset:
            wallet.balance = wallet.daily_allowance
            from django.utils import timezone
            wallet.last_refreshed_at = timezone.now()
            wallet.save(update_fields=["balance", "last_refreshed_at", "updated_at"])
            count += 1
        self.message_user(request, f"{count} wallet(s) refreshed.")


@admin.register(CreditUsageLog)
class CreditUsageLogAdmin(admin.ModelAdmin):
    list_display = ("user", "feature", "amount", "balance_after", "created_at")
    list_filter = ("feature",)
    search_fields = ("user__username", "feature")
    readonly_fields = ("user", "feature", "amount", "balance_after", "created_at")

    def has_add_permission(self, request):
        # Logs are created programmatically only.
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "razorpay_order_id",
        "amount_in_paise",
        "status",
        "created_at",
    )
    list_filter = ("status", "plan")
    search_fields = (
        "user__username",
        "user__email",
        "razorpay_order_id",
        "razorpay_payment_id",
    )
    autocomplete_fields = ("user", "plan")
    readonly_fields = (
        "user",
        "plan",
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "amount_in_paise",
        "currency",
        "status",
        "failure_reason",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        # Transactions are created via the payment flow only.
        return False