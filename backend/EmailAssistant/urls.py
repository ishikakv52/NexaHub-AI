from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "emailassistant"

urlpatterns = [
    # 🔧 TEMPORARY signup/login (accounts app se independent, testing ke liye)
    path("signup/", views.signup_view, name="signup"),
    path("login/", auth_views.LoginView.as_view(
        template_name="registration/login.html"
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/email-assistant/login/"), name="logout"),

    # Existing routes
    path("gmail-setup/", views.gmail_setup_view, name="gmail_setup"),
    path("", views.email_form_view, name="form"),
    path("preview/", views.email_preview_view, name="preview"),
    path("confirm/", views.email_confirm_view, name="confirm"),
    path("history/", views.email_history_view, name="history"),
]