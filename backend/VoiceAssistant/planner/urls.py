from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('diet-plan/', views.diet_plan_view, name='diet_plan'),
    path('food-library/', views.food_library_view, name='food_library'),
    path('grocery-list/', views.grocery_list_view, name='grocery_list'),
    path('progress/', views.progress_view, name='progress'),
    path('water/add/', views.add_water, name='add_water'),
    path('meal/<int:meal_id>/toggle/', views.toggle_meal_completion, name='toggle_meal_completion'),
]
