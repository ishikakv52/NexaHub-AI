from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # ── Auth ──────────────────────────────────
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('profile/', views.profile_view, name='profile'),

    # ── Dashboard ─────────────────────────────
    path('', views.dashboard_view, name='dashboard'),

    # ── Tasks ─────────────────────────────────
    path('tasks/', views.all_tasks_view, name='all_tasks'),
    path('tasks/today/', views.today_tasks_view, name='today_tasks'),
    path('tasks/completed/', views.completed_tasks_view, name='completed_tasks'),
    path('tasks/pending/', views.pending_tasks_view, name='pending_tasks'),
    path('tasks/overdue/', views.overdue_tasks_view, name='overdue_tasks'),
    path('tasks/add/', views.add_task_view, name='add_task'),
    path('tasks/<int:pk>/', views.task_detail_view, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.edit_task_view, name='edit_task'),
    path('tasks/<int:pk>/delete/', views.delete_task_view, name='delete_task'),
    path('tasks/<int:pk>/complete/', views.mark_complete_view, name='mark_complete'),
    path('tasks/<int:pk>/pending/', views.mark_pending_view, name='mark_pending'),

    # ── Categories ────────────────────────────
    path('categories/', views.categories_view, name='categories'),
    path('categories/<int:pk>/edit/', views.edit_category_view, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category_view, name='delete_category'),
]