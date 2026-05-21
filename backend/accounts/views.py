from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
import json
import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from accounts.models import *
from django.conf import settings
from config.settings import *
from .models import OTPModel
from django.views.decorators.csrf import csrf_exempt
OTP_STORE = {}
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
import json
from django.views.decorators.csrf import csrf_exempt
# 1. SEND OTP
@csrf_exempt
# STEP 1: SEND OTP
def forgot_password(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        print(f"[forgot_password] email={email}")

        try:
            user = User.objects.get(email=email)

            otp = random.randint(100000, 999999)
            OTP_STORE[email] = otp

            try:
                send_mail(
                    "Your OTP Code",
                    f"Your OTP is {otp}",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
                return JsonResponse({"message": "OTP sent"})
            except Exception as e:
                print(f"Email sending error: {str(e)}")
                return JsonResponse({"error": f"Failed to send OTP: {str(e)}"}, status=500)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Only POST allowed"})


# STEP 2: VERIFY OTP
@csrf_exempt
def verify_otp(request):

    if request.method == "POST":

        data = json.loads(request.body)

        email = data.get("email")
        otp = str(data.get("otp"))

        if (
            email in OTP_STORE
            and str(OTP_STORE[email]) == otp
        ):

            return JsonResponse({
                "message": "OTP verified"
            })

        return JsonResponse({
            "error": "Invalid OTP"
        }, status=400)

    return JsonResponse({
        "error": "Only POST allowed"
    })

# STEP 3: RESET PASSWORD
@csrf_exempt
def reset_password(request):
    if request.method == "POST":
        data = json.loads(request.body)

        email = data.get("email")
        new_password = data.get("password")

        try:
            user = User.objects.get(email=email)
            user.password = make_password(new_password)
            user.save()

            OTP_STORE.pop(email, None)

            return JsonResponse({"message": "Password updated"})

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Only POST allowed"})
@csrf_exempt






# =========================
# STEP 1: SEND OTP
# =========================
@csrf_exempt








@csrf_exempt
def send_signup_otp(request):

    if request.method == "POST":

        try:
            data = json.loads(request.body)

            email = data.get("email")
            username = data.get("username")

            if not email or not username:
                return JsonResponse({
                    "error": "Email and username required"
                }, status=400)

            otp = str(random.randint(100000, 999999))

            request.session["signup_otp"] = otp
            request.session["signup_email"] = email

            send_mail(
                subject="NEXA HUB AI OTP",
                message=f"Your OTP is: {otp}",
                from_email="ainexahub@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )

            return JsonResponse({
                "message": "OTP sent successfully"
            })

        except Exception as e:

            return JsonResponse({
                "error": str(e)
            }, status=500)

    return JsonResponse({
        "error": "Only POST method allowed"
    }, status=405)
# =========================
# STEP 2: VERIFY OTP
# =========================
@csrf_exempt
def verify_signup_otp(request):
    if request.method == "POST":
        data = json.loads(request.body)

        email = data.get("email")
        otp = data.get("otp")

        try:
            obj = OTPModel.objects.get(email=email)

            if obj.otp == otp:
                obj.is_verified = True
                obj.save()

                return JsonResponse({"message": "OTP verified"})
            else:
                return JsonResponse({"error": "Invalid OTP"}, status=400)

        except OTPModel.DoesNotExist:
            return JsonResponse({"error": "OTP not found"}, status=404)


# =========================
# STEP 3: FINAL SIGNUP
# =========================
from django.contrib.auth.models import User

@csrf_exempt
def signup(request):
    if request.method == "POST":
        data = json.loads(request.body)

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return JsonResponse({"error": "Missing fields"}, status=400)

        try:
            otp_obj = OTPModel.objects.get(email=email)

            if not otp_obj.is_verified:
                return JsonResponse({"error": "OTP not verified"}, status=400)

        except OTPModel.DoesNotExist:
            return JsonResponse({"error": "OTP not found"}, status=404)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email exists"}, status=400)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        otp_obj.delete()

        return JsonResponse({"message": "User created successfully"})