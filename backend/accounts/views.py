from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import json


def signup_view(request):

    if request.method == "POST":

        data = json.loads(request.body)

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if User.objects.filter(username=username).exists():

            return JsonResponse({
                "error": "Username already exists"
            }, status=400)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        return JsonResponse({
            "message": "Account created successfully"
        })

    return JsonResponse({
        "error": "Only POST method allowed"
    })


def login_view(request):

    if request.method == "POST":

        data = json.loads(request.body)

        username = data.get("username")
        password = data.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return JsonResponse({
                "message": "Login successful"
            })

        return JsonResponse({
            "error": "Invalid username or password"
        }, status=400)

    return JsonResponse({
        "error": "Only POST method allowed"
    })


def logout_view(request):

    logout(request)

    return JsonResponse({
        "message": "Logged out successfully"
    })