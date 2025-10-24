# central/views.py
import datetime
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.views.decorators.http import require_POST
from central.models import Admin
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import Admin
import datetime

def logout_user(request):
    request.session.flush()
    return redirect("/")


def _home_url():
    try:
        return reverse("home:home")
    except NoReverseMatch:
        return "/"

def _login_url():
    for name in ("central:login", "home:login", getattr(settings, "LOGIN_URL", "/login/")):
        try:
            return reverse(name)
        except NoReverseMatch:
            continue
    return "/login/"

def login_user(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(_home_url())
    return render(request, "login.html")

def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(_home_url())
    return render(request, "register.html")


@require_POST
def login_ajax(request):
    name = request.POST.get("username")
    password = request.POST.get("password")

    # ==== LOGIN SEBAGAI ADMIN ====
    try:
        admin = Admin.objects.get(name=name)
        if admin.check_password(password):
            # --- TAMBAHKAN INI ---
            # Logout dulu user bawaan (jika ada) agar session bersih
            logout(request)
            # ---------------------

            # Set session admin
            request.session["is_admin"] = True
            request.session["admin_name"] = admin.name

            # Buat response sukses
            resp = JsonResponse({
                "ok": True,
                "redirect": "/",
                "username": admin.name,
                "role": "admin",
            })
            resp.set_cookie("last_login", str(datetime.datetime.now()))
            return resp
    except Admin.DoesNotExist:
        pass

    # ==== LOGIN SEBAGAI USER BIASA ====
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)

        # --- TAMBAHKAN INI ---
        # Pastikan status admin bersih saat user biasa login
        request.session["is_admin"] = False
        if "admin_name" in request.session:
            del request.session["admin_name"]
        # ---------------------

        resp = JsonResponse({
            "ok": True,
            "redirect": "/",
            "username": user.username,
            "role": "user",
        })
        resp.set_cookie("last_login", str(datetime.datetime.now()))
        return resp

    # ==== GAGAL LOGIN ====
    return JsonResponse(
        {"ok": False, "errors": {"login": ["Username atau password salah."]}},
        status=400
    )

@require_POST
def register_ajax(request):
    form = UserCreationForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True, "redirect": _login_url()})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@require_POST
def logout_ajax(request):
    logout(request)
    return JsonResponse({"ok": True, "redirect": _home_url()})
