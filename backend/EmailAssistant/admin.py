from django.contrib import admin
from .models import GmailConfig, EmailHistory


@admin.register(GmailConfig)
class GmailConfigAdmin(admin.ModelAdmin):
    list_display  = ("user", "masked_password", "updated_at")
    readonly_fields = ("updated_at",)
    search_fields = ("user__email", "user__username")

    def masked_password(self, obj):
        """Show only last 4 chars for safety in the admin list."""
        pwd = obj.app_password or ""
        return "•" * (len(pwd) - 4) + pwd[-4:] if len(pwd) >= 4 else "••••"
    masked_password.short_description = "App Password"


@admin.register(EmailHistory)
class EmailHistoryAdmin(admin.ModelAdmin):
    list_display   = ("subject", "sender_email", "receiver_email", "status", "created_at", "user")
    list_filter    = ("status", "category", "tone", "premium_level")
    search_fields  = ("subject", "receiver_email", "sender_email", "topic")
    readonly_fields = ("created_at",)
