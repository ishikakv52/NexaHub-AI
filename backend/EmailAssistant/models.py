"""
models.py - AI Email Assistant

Two models:
  1. GmailConfig  -> stores the user's Gmail address (auto-fetched from
                     request.user.email) and their Gmail App Password so
                     we can send emails on their behalf via SMTP without
                     touching the project-wide EMAIL_* settings.

  2. EmailHistory -> one row per sent/failed email, linked to the user.
"""

from django.db import models
from django.conf import settings


class GmailConfig(models.Model):
    """
    Stores one Gmail App Password per user.
    The Gmail address is always taken from request.user.email — the user
    never types it here; it is shown read-only for confirmation only.

    Security note: the app_password is stored as plain text in the DB.
    For production you would encrypt it with django-encrypted-model-fields
    or similar, but for this offline project plain text keeps it simple
    and beginner-friendly.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gmail_config",
    )

    # The 16-character Gmail App Password (spaces stripped on save)
    app_password = models.CharField(max_length=64)

    # When was it saved / last updated
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GmailConfig for {self.user.email}"

    def clean_password(self):
        """Return password with spaces stripped (Google shows it with spaces)."""
        return self.app_password.replace(" ", "")


class EmailHistory(models.Model):
    """
    One row = one email the user generated and attempted to send.
    Linked to the logged-in user so people only ever see their own history.
    """

    STATUS_CHOICES = [
        ("SENT", "Sent"),
        ("FAILED", "Failed"),
    ]

    CATEGORY_CHOICES = [
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
    ]

    TONE_CHOICES = [
        ("Professional", "Professional"),
        ("Friendly", "Friendly"),
        ("Formal", "Formal"),
        ("Confident", "Confident"),
        ("Polite", "Polite"),
        ("Persuasive", "Persuasive"),
        ("Respectful", "Respectful"),
        ("Apologetic", "Apologetic"),
        ("Simple", "Simple"),
    ]

    LENGTH_CHOICES = [
        ("Small", "Small"),
        ("Medium", "Medium"),
        ("Large", "Large"),
    ]

    LEVEL_CHOICES = [
        ("Basic", "Basic"),
        ("Premium", "Premium"),
        ("Premium Plus", "Premium Plus"),
    ]

    # Who sent it (also kept as plain text for quick display/search)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_history",
    )
    sender_email = models.EmailField()
    receiver_email = models.EmailField()

    subject = models.CharField(max_length=255)
    body = models.TextField()

    topic = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="General")
    tone = models.CharField(max_length=50, choices=TONE_CHOICES, default="Professional")
    length = models.CharField(max_length=20, choices=LENGTH_CHOICES, default="Medium")
    premium_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="Basic")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="FAILED")
    error_message = models.CharField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # newest first by default

    def __str__(self):
        return f"{self.subject} -> {self.receiver_email} ({self.status})"
