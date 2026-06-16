# Generated initial migration for the subscriptions app.
# Run: python manage.py migrate subscriptions

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("plan_type", models.CharField(choices=[("free", "Free"), ("premium", "Premium")], default="premium", max_length=20)),
                ("description", models.TextField(blank=True)),
                ("price_in_paise", models.PositiveIntegerField(default=0, help_text="Price in paise (e.g. \u20b9199 = 19900). Set 0 for free plans.")),
                ("currency", models.CharField(default="INR", max_length=10)),
                ("duration_days", models.PositiveIntegerField(default=30, help_text="Number of days premium access remains active after purchase.")),
                ("daily_credits", models.PositiveIntegerField(default=1200, help_text="Steady-state daily credit allowance (from day 2 onwards).")),
                ("signup_bonus_credits", models.PositiveIntegerField(default=2000, help_text="One-time credit amount given on the user's first day (day of signup). From day 2 onwards, daily_credits applies.")),
                ("is_unlimited", models.BooleanField(default=False, help_text="If True, users on this plan bypass all credit checks.")),
                ("is_active", models.BooleanField(default=True, help_text="Inactive plans are hidden from purchase but preserved for history.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Subscription Plan",
                "verbose_name_plural": "Subscription Plans",
                "ordering": ["price_in_paise"],
            },
        ),
        migrations.CreateModel(
            name="UserSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("active", "Active"), ("expired", "Expired"), ("cancelled", "Cancelled")], default="active", max_length=20)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField(blank=True, help_text="Null/blank means no expiry (e.g. permanent free plan).", null=True)),
                ("auto_downgraded", models.BooleanField(default=False, help_text="Set to True once an expired premium plan has been auto-downgraded.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="subscriptions.subscriptionplan")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="subscription", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "User Subscription",
                "verbose_name_plural": "User Subscriptions",
            },
        ),
        migrations.CreateModel(
            name="CreditWallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("balance", models.PositiveIntegerField(default=0)),
                ("daily_allowance", models.PositiveIntegerField(default=1200, help_text="Snapshot of the plan's daily credit allowance.")),
                ("last_refreshed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("has_received_signup_bonus", models.BooleanField(default=False, help_text="True once the one-time signup bonus has been granted (on wallet creation / first refresh).")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="credit_wallet", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Credit Wallet",
                "verbose_name_plural": "Credit Wallets",
            },
        ),
        migrations.CreateModel(
            name="CreditUsageLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.PositiveIntegerField(default=1)),
                ("feature", models.CharField(help_text="Identifier for the feature/endpoint that consumed credits, e.g. 'remedies.ai_chat', 'workout.generate_plan'.", max_length=100)),
                ("balance_after", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="credit_usage_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Credit Usage Log",
                "verbose_name_plural": "Credit Usage Logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="creditusagelog",
            index=models.Index(fields=["user", "created_at"], name="subscriptio_user_id_e3f3e0_idx"),
        ),
        migrations.CreateModel(
            name="PaymentTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("razorpay_order_id", models.CharField(max_length=100, unique=True)),
                ("razorpay_payment_id", models.CharField(blank=True, max_length=100, null=True)),
                ("razorpay_signature", models.CharField(blank=True, max_length=255, null=True)),
                ("amount_in_paise", models.PositiveIntegerField()),
                ("currency", models.CharField(default="INR", max_length=10)),
                ("status", models.CharField(choices=[("created", "Order Created"), ("paid", "Paid / Verified"), ("failed", "Failed")], default="created", max_length=20)),
                ("failure_reason", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_transactions", to="subscriptions.subscriptionplan")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payment_transactions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Payment Transaction",
                "verbose_name_plural": "Payment Transactions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["user", "status"], name="subscriptio_user_id_8f1a2b_idx"),
        ),
    ]