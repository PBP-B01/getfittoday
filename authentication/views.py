import json
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from central.models import Admin

@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                "status": False,
                "message": "Invalid request method.",
            },
            status=400,
        )

    username = request.POST.get('username')
    password = request.POST.get('password')

    if not username or not password:
        return JsonResponse(
            {
                "status": False,
                "message": "Username and password are required.",
            },
            status=400,
        )

    try:
        admin = Admin.objects.get(name=username)
        if admin.check_password(password):
            auth_logout(request)
            request.session["is_admin"] = True
            request.session["admin_name"] = admin.name
            return JsonResponse(
                {
                    "username": admin.name,
                    "status": True,
                    "message": "Login successful!",
                    "is_admin": True,
                    "role": "admin",
                },
                status=200,
            )
    except Admin.DoesNotExist:
        pass

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            request.session["is_admin"] = False
            if "admin_name" in request.session:
                del request.session["admin_name"]
            return JsonResponse(
                {
                    "username": user.username,
                    "status": True,
                    "message": "Login successful!",
                    "is_admin": bool(user.is_staff or user.is_superuser),
                    "is_staff": bool(user.is_staff),
                    "is_superuser": bool(user.is_superuser),
                    "role": "user",
                },
                status=200,
            )

        return JsonResponse(
            {
                "status": False,
                "message": "Login failed, account is disabled.",
            },
            status=401,
        )

    return JsonResponse(
        {
            "status": False,
            "message": "Login failed, please check your username or password.",
        },
        status=401,
    )

@csrf_exempt
def logout(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                "status": False,
                "message": "Invalid request method.",
            },
            status=400,
        )

    auth_logout(request)
    return JsonResponse(
        {
            "status": True,
            "message": "Logout successful!",
        },
        status=200,
    )


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                "status": False,
                "message": "Invalid request method.",
            },
            status=400,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": False,
                "message": "Invalid JSON payload.",
            },
            status=400,
        )

    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2')

    if not username or not password1 or not password2:
        return JsonResponse(
            {
                "status": False,
                "message": "All fields are required.",
            },
            status=400,
        )

    if password1 != password2:
        return JsonResponse(
            {
                "status": False,
                "message": "Passwords do not match.",
            },
            status=400,
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {
                "status": False,
                "message": "Username already exists.",
            },
            status=400,
        )

    user = User.objects.create_user(username=username, password=password1)
    user.save()

    return JsonResponse(
        {
            "username": user.username,
            "status": 'success',
            "message": "User created successfully!",
        },
        status=200,
    )
