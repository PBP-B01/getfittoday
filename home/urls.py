from django.urls import path, include
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),

    path('api/map-boundaries/', views.api_map_boundaries, name='api_map_boundaries'),
    path('api/fitness-spots/', views.api_fitness_spots, name='api_fitness_spots'),

    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register, name='register'),

    path("login/ajax/", views.login_ajax, name="login_ajax"),
    path("register/ajax/", views.register_ajax, name="register_ajax"),
    path("logout/ajax/", views.logout_ajax, name="logout_ajax"),
]
