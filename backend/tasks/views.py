from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Task, Category
from .forms import (
    SignupForm, LoginForm, ProfileUpdateForm, ForgotPasswordForm,
    CategoryForm, TaskForm, TaskFilterForm
)


# ════════════════════════════════════════════════════════
# AUTH VIEWS
# ════════════════════════════════════════════════════════

def signup_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        print(form.errors)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}! Account created successfully.")
            return redirect('tasks:dashboard')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SignupForm()

    return render(request, 'tasks/signup.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('tasks:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'tasks/login.html', {'form': form})


def logout_view(request):
    """User logout"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect('tasks:login')


def forgot_password_view(request):
    """Simple password reset (no email needed)"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            new_password = form.cleaned_data['new_password']
            try:
                user = User.objects.get(username=username)
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password updated! Please login with your new password.")
                return redirect('tasks:login')
            except User.DoesNotExist:
                messages.error(request, "No account found with that username.")
    else:
        form = ForgotPasswordForm()

    return render(request, 'tasks/forgot_password.html', {'form': form})


@login_required(login_url='tasks:login')
def profile_view(request):
    """View and update user profile"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('tasks:profile')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'tasks/profile.html', {'form': form})


# ════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════

@login_required(login_url='tasks:login')
def dashboard_view(request):
    """Main dashboard with stats and recent tasks"""
    today = timezone.now().date()
    user = request.user

    all_tasks = Task.objects.filter(user=user)
    total = all_tasks.count()
    pending = all_tasks.filter(status='pending').count()
    completed = all_tasks.filter(status='completed').count()
    today_tasks = all_tasks.filter(due_date=today).count()
    high_priority = all_tasks.filter(priority='high', status='pending').count()
    overdue = all_tasks.filter(due_date__lt=today, status='pending').count()

    recent_tasks = all_tasks.order_by('-created_at')[:5]
    upcoming_tasks = all_tasks.filter(due_date__gte=today, status='pending').order_by('due_date')[:5]

    context = {
        'total': total,
        'pending': pending,
        'completed': completed,
        'today_tasks': today_tasks,
        'high_priority': high_priority,
        'overdue': overdue,
        'recent_tasks': recent_tasks,
        'upcoming_tasks': upcoming_tasks,
        'today': today,
    }
    return render(request, 'tasks/dashboard.html', context)


# ════════════════════════════════════════════════════════
# TASK VIEWS
# ════════════════════════════════════════════════════════

def get_filtered_tasks(request, queryset):
    """Helper to apply search, filter, and sort to a queryset"""
    form = TaskFilterForm(user=request.user, data=request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        priority = form.cleaned_data.get('priority')
        status = form.cleaned_data.get('status')
        sort = form.cleaned_data.get('sort') or '-created_at'

        if search:
            queryset = queryset.filter(title__icontains=search)
        if category:
            queryset = queryset.filter(category=category)
        if priority:
            queryset = queryset.filter(priority=priority)
        if status:
            queryset = queryset.filter(status=status)

        # Priority sorting needs custom ordering
        if sort == '-priority':
            from django.db.models import Case, When, IntegerField
            queryset = queryset.annotate(
                priority_order=Case(
                    When(priority='high', then=1),
                    When(priority='medium', then=2),
                    When(priority='low', then=3),
                    output_field=IntegerField(),
                )
            ).order_by('priority_order')
        else:
            queryset = queryset.order_by(sort)
    return queryset, form


@login_required(login_url='tasks:login')
def all_tasks_view(request):
    """All tasks with search/filter/sort"""
    tasks = Task.objects.filter(user=request.user)
    tasks, filter_form = get_filtered_tasks(request, tasks)
    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks,
        'filter_form': filter_form,
        'page_title': 'All Tasks',
        'today': timezone.now().date(),
    })


@login_required(login_url='tasks:login')
def today_tasks_view(request):
    """Tasks due today"""
    today = timezone.now().date()
    tasks = Task.objects.filter(user=request.user, due_date=today)
    tasks, filter_form = get_filtered_tasks(request, tasks)
    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks,
        'filter_form': filter_form,
        'page_title': "Today's Tasks",
        'today': today,
    })


@login_required(login_url='tasks:login')
def completed_tasks_view(request):
    """Completed tasks"""
    tasks = Task.objects.filter(user=request.user, status='completed')
    tasks, filter_form = get_filtered_tasks(request, tasks)
    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks,
        'filter_form': filter_form,
        'page_title': 'Completed Tasks',
        'today': timezone.now().date(),
    })


@login_required(login_url='tasks:login')
def pending_tasks_view(request):
    """Pending tasks"""
    tasks = Task.objects.filter(user=request.user, status='pending')
    tasks, filter_form = get_filtered_tasks(request, tasks)
    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks,
        'filter_form': filter_form,
        'page_title': 'Pending Tasks',
        'today': timezone.now().date(),
    })


@login_required(login_url='tasks:login')
def overdue_tasks_view(request):
    """Overdue tasks: past due date and still pending"""
    today = timezone.now().date()
    tasks = Task.objects.filter(user=request.user, due_date__lt=today, status='pending')
    tasks, filter_form = get_filtered_tasks(request, tasks)
    return render(request, 'tasks/all_tasks.html', {
        'tasks': tasks,
        'filter_form': filter_form,
        'page_title': 'Overdue Tasks',
        'today': today,
    })


@login_required(login_url='tasks:login')
def add_task_view(request):
    """Create a new task"""
    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" added successfully!')
            return redirect('tasks:all_tasks')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TaskForm(user=request.user)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'page_title': 'Add Task',
        'btn_label': 'Add Task',
    })


@login_required(login_url='tasks:login')
def edit_task_view(request, pk):
    """Edit an existing task"""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('tasks:task_detail', pk=pk)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TaskForm(user=request.user, instance=task)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'task': task,
        'page_title': 'Edit Task',
        'btn_label': 'Save Changes',
    })


@login_required(login_url='tasks:login')
def task_detail_view(request, pk):
    """View full task details"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    today = timezone.now().date()
    return render(request, 'tasks/task_detail.html', {'task': task, 'today': today})


@login_required(login_url='tasks:login')
def delete_task_view(request, pk):
    """Confirm and delete a task"""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted successfully.')
        return redirect('tasks:all_tasks')

    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required(login_url='tasks:login')
def mark_complete_view(request, pk):
    """Mark a task as completed"""
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.status = 'completed'
        task.save()
        messages.success(request, f'"{task.title}" marked as completed!')
    return redirect(request.META.get('HTTP_REFERER', 'tasks:all_tasks'))


@login_required(login_url='tasks:login')
def mark_pending_view(request, pk):
    """Mark a task as pending"""
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.status = 'pending'
        task.save()
        messages.success(request, f'"{task.title}" marked as pending.')
    return redirect(request.META.get('HTTP_REFERER', 'tasks:all_tasks'))


# ════════════════════════════════════════════════════════
# CATEGORY VIEWS
# ════════════════════════════════════════════════════════

@login_required(login_url='tasks:login')
def categories_view(request):
    """List all categories and handle add/edit inline"""
    categories = Category.objects.filter(user=request.user)
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" added!')
            return redirect('tasks:categories')
        else:
            messages.error(request, "Could not add category.")

    return render(request, 'tasks/categories.html', {
        'categories': categories,
        'form': form,
    })


@login_required(login_url='tasks:login')
def edit_category_view(request, pk):
    """Edit a category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category updated to "{category.name}".')
            return redirect('tasks:categories')
        else:
            messages.error(request, "Could not update category.")
    else:
        form = CategoryForm(instance=category)

    return render(request, 'tasks/edit_category.html', {
        'form': form,
        'category': category,
    })


@login_required(login_url='tasks:login')
def delete_category_view(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('tasks:categories')

    return render(request, 'tasks/category_confirm_delete.html', {'category': category})