"""
subscriptions/urls.py
"""

from django.urls import path

from .views import (
    CreateOrderView,
    RazorpayWebhookView,
    SubscriptionPlanListView,
    SubscriptionStatusView,
    VerifyPaymentView,
    credits_page,
)

app_name = "subscriptions"

urlpatterns = [
    path("plans/", SubscriptionPlanListView.as_view(), name="plan-list"),
    path("status/", SubscriptionStatusView.as_view(), name="status"),
    path("create-order/", CreateOrderView.as_view(), name="create-order"),
    path("verify-payment/", VerifyPaymentView.as_view(), name="verify-payment"),
    path("webhook/", RazorpayWebhookView.as_view(), name="webhook"),
    path("credits-page/", credits_page, name="credits-page"),
]