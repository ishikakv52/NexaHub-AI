# backend/VoiceAssistant/admin.py
from django.contrib import admin
# from . import models
# from .models import *

# # Helper to safely register a model if it exists in models.py
# def safe_register(model_name, admin_class=None, **admin_kwargs):
#     model = getattr(models, model_name, None)
#     if model is None:
#         return
#     if admin_class:
#         admin.site.register(model, admin_class)
#     else:
#         admin.site.register(model)

# # Simple admin classes (customize fields as needed)
# class SimpleModelAdmin(admin.ModelAdmin):
#     pass

# class ReadOnlyTimestampAdmin(admin.ModelAdmin):
#     readonly_fields = ("created_at", "sent_at", "detected_at", "trained_at")
# @admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
#     list_display = ("title", "user", "done", "created_at", "due_date")
#     search_fields = ("title", "user__username")
#     list_filter = ("done", "created_at")

# # Register models only if they are defined
# safe_register("UserProfile", SimpleModelAdmin)
# safe_register("Conversation", SimpleModelAdmin)
# safe_register("IntentLog", SimpleModelAdmin)
# safe_register("Task", SimpleModelAdmin)            # will be skipped if Task not defined
# safe_register("Reminder", SimpleModelAdmin)
# safe_register("HealthMetric", SimpleModelAdmin)
# safe_register("HealthGoal", SimpleModelAdmin)
# safe_register("WorkoutSession", SimpleModelAdmin)
# safe_register("MealLog", SimpleModelAdmin)
# safe_register("DeviceSync", SimpleModelAdmin)
# safe_register("Notification", SimpleModelAdmin)
# safe_register("IntentModelMeta", SimpleModelAdmin)
# safe_register("EmailLog", ReadOnlyTimestampAdmin)
# safe_register("AuditLog", SimpleModelAdmin)

# # Fallback: if you prefer explicit control, uncomment and adjust the lines below
# # (useful when you know exactly which models exist)
# # try:
# #     admin.site.register(models.Task, SimpleModelAdmin)
# # except AttributeError:
# #     pass