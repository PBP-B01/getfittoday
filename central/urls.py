from django.urls import path
from . import views

app_name = "central"

urlpatterns = [
    path("login/", views.login_user, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_user, name="logout"),

    path("login/ajax/", views.login_ajax, name="login_ajax"),
    path("register/ajax/", views.register_ajax, name="register_ajax"),
    path("logout/ajax/", views.logout_ajax, name="logout_ajax"),

]
