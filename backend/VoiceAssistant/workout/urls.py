from django.urls import path

from . import views


urlpatterns = [
    path("", views.workout_home, name="home"),
    path("api/generate/", views.generate_plan, name="generate_plan"),
    path("api/feedback/", views.submit_feedback, name="submit_feedback"),
    path("api/health/", views.health_check, name="health_check"),
]