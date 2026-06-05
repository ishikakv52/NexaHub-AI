from django.urls import path
from .views import process_remedy, ai_chat

urlpatterns = [
    # =========================
    # MAIN AI API ENDPOINT
    # =========================
    path('process/', process_remedy, name='process_remedy'),

    # =========================
    # CHAT FRONTEND
    # =========================
    path('chat/', ai_chat, name='ai_chat'),
]