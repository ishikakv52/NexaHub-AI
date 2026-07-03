"""
0001_initial.py
Auto-generated initial migration for the EmailAssistant app.
Run:  python manage.py migrate
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sender_email", models.EmailField(max_length=254)),
                ("receiver_email", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("topic", models.CharField(max_length=200)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("Professional", "Professional"),
                            ("Business", "Business"),
                            ("Formal", "Formal"),
                            ("Friendly", "Friendly"),
                            ("Personal", "Personal"),
                            ("Academic", "Academic"),
                            ("Marketing", "Marketing"),
                            ("Customer Support", "Customer Support"),
                            ("HR", "HR"),
                            ("Sales", "Sales"),
                            ("General", "General"),
                        ],
                        default="General",
                        max_length=50,
                    ),
                ),
                (
                    "tone",
                    models.CharField(
                        choices=[
                            ("Professional", "Professional"),
                            ("Friendly", "Friendly"),
                            ("Formal", "Formal"),
                            ("Confident", "Confident"),
                            ("Polite", "Polite"),
                            ("Persuasive", "Persuasive"),
                            ("Respectful", "Respectful"),
                            ("Apologetic", "Apologetic"),
                            ("Simple", "Simple"),
                        ],
                        default="Professional",
                        max_length=50,
                    ),
                ),
                (
                    "length",
                    models.CharField(
                        choices=[
                            ("Small", "Small"),
                            ("Medium", "Medium"),
                            ("Large", "Large"),
                        ],
                        default="Medium",
                        max_length=20,
                    ),
                ),
                (
                    "premium_level",
                    models.CharField(
                        choices=[
                            ("Basic", "Basic"),
                            ("Premium", "Premium"),
                            ("Premium Plus", "Premium Plus"),
                        ],
                        default="Basic",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("SENT", "Sent"), ("FAILED", "Failed")],
                        default="FAILED",
                        max_length=10,
                    ),
                ),
                (
                    "error_message",
                    models.CharField(blank=True, max_length=500, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_history",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
