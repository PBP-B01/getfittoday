from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api/fitness-spots/', views.get_fitness_spots_data, name='get_fitness_spots_data'),
    path('api/map-boundaries/', views.get_map_boundaries, name='get_map_boundaries'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register, name='register'),
]
