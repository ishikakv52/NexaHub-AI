"""
subscriptions/views.py

API endpoints for:
    - Listing available subscription plans
    - Getting current subscription/credit status
    - Creating a Razorpay order (initiate payment)
    - Verifying a Razorpay payment + activating premium

All views use DRF (already configured in this project via REST_FRAMEWORK
+ JWTAuthentication). Razorpay credentials are read from environment
variables (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET) — never hardcoded.
"""

import hashlib
import hmac
import logging
import os
from django.shortcuts import render
import razorpay
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentTransaction, SubscriptionPlan
from .serializers import (
    PaymentTransactionSerializer,
    SubscriptionPlanSerializer,
    SubscriptionStatusSerializer,
    VerifyPaymentSerializer,
)
from .services import get_or_create_subscription, get_subscription_status

logger = logging.getLogger(__name__)


def get_razorpay_client():
    """
    Lazily constructs the Razorpay client using credentials from the
    environment. Raises a clear error if not configured, instead of
    failing with a cryptic Razorpay SDK error.
    """
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError(
            "Razorpay credentials are not configured. "
            "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in your .env file."
        )

    return razorpay.Client(auth=(key_id, key_secret))


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
class SubscriptionPlanListView(APIView):
    """
    GET /api/subscriptions/plans/

    Returns all active subscription plans (excludes the internal Free
    plan from the "purchasable" list, but includes it for completeness —
    frontend can filter by plan_type if desired).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
class SubscriptionStatusView(APIView):
    """
    GET /api/subscriptions/status/

    Returns the authenticated user's current subscription + credit status.
    This is the lazy sync point — calling this endpoint will:
        - auto-downgrade expired premium subscriptions
        - refresh daily credits if a new day has started
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_subscription_status(request.user)
        serializer = SubscriptionStatusSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Create Razorpay Order
# ---------------------------------------------------------------------------
class CreateOrderView(APIView):
    """
    POST /api/subscriptions/create-order/
    Body: { "plan_id": <int> }

    Creates a Razorpay order for the given plan and a corresponding
    PaymentTransaction record with status=CREATED.

    Response includes everything the frontend needs to open Razorpay
    Checkout (order_id, amount, currency, key_id).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return Response(
                {"detail": "plan_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"detail": "Invalid or inactive plan."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if plan.plan_type != SubscriptionPlan.PlanType.PREMIUM:
            return Response(
                {"detail": "Only premium plans can be purchased."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = get_razorpay_client()
        except RuntimeError as exc:
            logger.error("Razorpay client init failed: %s", exc)
            return Response(
                {"detail": "Payment gateway is not configured. Contact support."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            razorpay_order = client.order.create(
                {
                    "amount": plan.price_in_paise,
                    "currency": plan.currency,
                    "payment_capture": 1,
                    "notes": {
                        "user_id": str(request.user.id),
                        "username": request.user.username,
                        "plan_id": str(plan.id),
                        "plan_name": plan.name,
                    },
                }
            )
        except Exception as exc:  # Razorpay SDK can raise various errors
            logger.exception("Razorpay order creation failed")
            return Response(
                {"detail": "Failed to create payment order. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        transaction_record = PaymentTransaction.objects.create(
            user=request.user,
            plan=plan,
            razorpay_order_id=razorpay_order["id"],
            amount_in_paise=plan.price_in_paise,
            currency=plan.currency,
            status=PaymentTransaction.Status.CREATED,
        )

        return Response(
            {
                "order_id": razorpay_order["id"],
                "amount": plan.price_in_paise,
                "currency": plan.currency,
                "key_id": os.getenv("RAZORPAY_KEY_ID"),
                "plan": SubscriptionPlanSerializer(plan).data,
                "transaction_id": transaction_record.id,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Verify Razorpay Payment
# ---------------------------------------------------------------------------
class VerifyPaymentView(APIView):
    """
    POST /api/subscriptions/verify-payment/
    Body: {
        "razorpay_order_id": "...",
        "razorpay_payment_id": "...",
        "razorpay_signature": "..."
    }

    Verifies the payment signature using HMAC-SHA256 (per Razorpay docs),
    and on success:
        - marks the PaymentTransaction as PAID
        - activates the premium subscription for the user
    On failure:
        - marks the transaction as FAILED
        - returns an error response
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        order_id = payload["razorpay_order_id"]
        payment_id = payload["razorpay_payment_id"]
        signature = payload["razorpay_signature"]

        try:
            transaction_record = PaymentTransaction.objects.select_related("plan", "user").get(
                razorpay_order_id=order_id,
                user=request.user,
            )
        except PaymentTransaction.DoesNotExist:
            return Response(
                {"detail": "Transaction not found for this order."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if transaction_record.status == PaymentTransaction.Status.PAID:
            # Idempotency: if already verified, just return current status.
            return Response(
                {
                    "detail": "Payment already verified.",
                    "subscription": get_subscription_status(request.user),
                },
                status=status.HTTP_200_OK,
            )

        key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        if not key_secret:
            logger.error("RAZORPAY_KEY_SECRET not configured during verification")
            return Response(
                {"detail": "Payment gateway is not configured. Contact support."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Razorpay signature verification:
        # expected_signature = HMAC_SHA256(order_id + "|" + payment_id, key_secret)
        message = f"{order_id}|{payment_id}".encode("utf-8")
        expected_signature = hmac.new(
            key_secret.encode("utf-8"), message, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            transaction_record.mark_failed(reason="Signature verification failed.")
            return Response(
                {"detail": "Payment verification failed. Invalid signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Signature valid -> mark paid + activate premium.
        transaction_record.mark_paid(payment_id=payment_id, signature=signature)

        subscription = get_or_create_subscription(request.user)
        subscription.activate_premium(transaction_record.plan)

        return Response(
            {
                "detail": "Payment verified. Premium activated.",
                "transaction": PaymentTransactionSerializer(transaction_record).data,
                "subscription": get_subscription_status(request.user),
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Payment Webhook (optional, recommended for production reliability)
# ---------------------------------------------------------------------------
class RazorpayWebhookView(APIView):
    """
    POST /api/subscriptions/webhook/

    Optional but recommended: Razorpay can call this endpoint directly
    for `payment.captured` / `payment.failed` events, providing a
    server-to-server fallback independent of the frontend redirect flow.

    To use this, set RAZORPAY_WEBHOOK_SECRET in your .env and configure
    the webhook URL in the Razorpay dashboard. If RAZORPAY_WEBHOOK_SECRET
    is not set, this endpoint safely no-ops (returns 200) so it won't
    break anything if unused.
    """

    # Webhooks are server-to-server; no user auth/JWT applies here.
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        if not webhook_secret:
            # Webhook not configured -> ignore gracefully.
            return Response({"detail": "Webhook not configured."}, status=status.HTTP_200_OK)

        signature = request.headers.get("X-Razorpay-Signature", "")
        body = request.body

        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            return Response({"detail": "Invalid webhook signature."}, status=status.HTTP_400_BAD_REQUEST)

        event = request.data.get("event")
        payload = request.data.get("payload", {})

        if event == "payment.captured":
            payment_entity = payload.get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")

            try:
                transaction_record = PaymentTransaction.objects.select_related("plan", "user").get(
                    razorpay_order_id=order_id
                )
            except PaymentTransaction.DoesNotExist:
                logger.warning("Webhook: unknown order_id %s", order_id)
                return Response({"detail": "Order not found."}, status=status.HTTP_200_OK)

            if transaction_record.status != PaymentTransaction.Status.PAID:
                transaction_record.razorpay_payment_id = payment_id
                transaction_record.status = PaymentTransaction.Status.PAID
                transaction_record.save(update_fields=["razorpay_payment_id", "status", "updated_at"])

                subscription = get_or_create_subscription(transaction_record.user)
                subscription.activate_premium(transaction_record.plan)

        elif event == "payment.failed":
            payment_entity = payload.get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            try:
                transaction_record = PaymentTransaction.objects.get(razorpay_order_id=order_id)
                transaction_record.mark_failed(reason="Razorpay reported payment.failed event.")
            except PaymentTransaction.DoesNotExist:
                logger.warning("Webhook: unknown order_id %s for failed payment", order_id)

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)
def credits_page(request):
    return render(request, "subscriptions/credits.html")