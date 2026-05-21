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
# OTP_STORE = {}
otp_storage = {}
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
            otp_storage[email] = otp

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
            email in otp_storage
            and str(otp_storage[email]) == otp
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

            otp_storage.pop(email, None)

            return JsonResponse({"message": "Password updated"})

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Only POST allowed"})






# =========================
# STEP 1: SEND OTP
# =========================

@csrf_exempt
def send_signup_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST method allowed"
        }, status=405)

    try:
        body = json.loads(request.body)

        email = body.get("email")
        username = body.get("username")

        if not email or not username:
            return JsonResponse({
                "error": "Email and username required"
            }, status=400)

        otp = str(random.randint(100000, 999999))

        otp_storage[email] = otp

        send_mail(
            subject="Nexa Hub AI OTP",
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
# =========================
# STEP 2: VERIFY OTP
# =========================





@csrf_exempt
def verify_signup_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST method allowed"
        }, status=405)

    try:
        body = json.loads(request.body)

        email = body.get("email")
        otp = body.get("otp")

        if not email or not otp:
            return JsonResponse({
                "error": "Email and OTP required"
            }, status=400)

        stored_otp = otp_storage.get(email)

        print("Entered OTP:", otp)
        print("Stored OTP:", stored_otp)

        if stored_otp and str(stored_otp) == str(otp):

            return JsonResponse({
                "message": "OTP verified successfully"
            }, status=200)

        return JsonResponse({
            "error": "Invalid OTP"
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)
# =========================
# STEP 3: FINAL SIGNUP
# =========================
from django.contrib.auth.models import User

@csrf_exempt

def signup(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST method allowed"
        }, status=405)

    try:
        body = json.loads(request.body)

        username = body.get("username")
        email = body.get("email")
        password = body.get("password")

        if not username or not email or not password:
            return JsonResponse({
                "error": "All fields are required"
            }, status=400)

        # check existing user
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "error": "Username already exists"
            }, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                "error": "Email already exists"
            }, status=400)

        # create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        return JsonResponse({
            "message": "Account created successfully"
        }, status=201)

    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)