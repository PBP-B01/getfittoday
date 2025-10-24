# central/views.py
import datetime
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.views.decorators.http import require_POST

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

def logout_user(request):
    logout(request)
    return redirect(_home_url())

@require_POST
def login_ajax(request):
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = (
            request.POST.get("next")
            or request.GET.get("next")
            or _home_url()
        )
        resp = JsonResponse({
            "ok": True,
            "redirect": next_url,
            "username": user.username,
        })
        resp.set_cookie("last_login", str(datetime.datetime.now()))
        return resp

    return JsonResponse(
        {"ok": False, "errors": form.errors},
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
