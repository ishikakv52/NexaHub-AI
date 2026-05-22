from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('signup/', views.signup_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
     # 🔐 NEW OTP ROUTES
    path('forgot-password/', views.forgot_password),
    path('verify-otp/', views.verify_otp),
    path('reset-password/', views.reset_password),
    path("send-signup-otp/", send_signup_otp),
    path("verify-signup-otp/", verify_signup_otp),
    path("signup/", signup),
    path('resend-signup-otp/', resend_signup_otp),
    path("auth/google/", views.google_login),
    path("auth/apple/", views.apple_login),
]