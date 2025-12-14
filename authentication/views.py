import json

from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            return JsonResponse(
                {
                    "username": user.username,
                    "status": True,
                    "message": "Login successful!",
                    "is_staff": user.is_staff,
                },
                status=200,
            )
        else:
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
