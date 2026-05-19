from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
     # 🔐 NEW OTP ROUTES
    path('forgot-password/', views.forgot_password),
    path('verify-otp/', views.verify_otp),
    path('reset-password/', views.reset_password),
]