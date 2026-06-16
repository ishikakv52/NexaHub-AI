"""
subscriptions/serializers.py

DRF serializers for the subscription/credit API responses and
payment verification request validation.
"""

from rest_framework import serializers

from .models import PaymentTransaction, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    price_in_rupees = serializers.FloatField(read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "name",
            "plan_type",
            "description",
            "price_in_paise",
            "price_in_rupees",
            "currency",
            "duration_days",
            "daily_credits",
            "is_unlimited",
            "is_active",
        ]


class SubscriptionStatusSerializer(serializers.Serializer):
    """
    Serializes the dict returned by services.get_subscription_status().
    """
    plan_name = serializers.CharField()
    plan_type = serializers.CharField()
    is_premium = serializers.BooleanField()
    is_unlimited = serializers.BooleanField()
    status = serializers.CharField()
    started_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)
    credits_remaining = serializers.IntegerField()
    daily_allowance = serializers.IntegerField()
    credits_last_refreshed_at = serializers.DateTimeField()


class PaymentTransactionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "plan_name",
            "razorpay_order_id",
            "razorpay_payment_id",
            "amount_in_paise",
            "currency",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class VerifyPaymentSerializer(serializers.Serializer):
    """
    Validates the payload sent by the frontend after Razorpay Checkout
    completes successfully.
    """
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=255)