from django.urls import path
from . import views

app_name = 'home' # Nama aplikasi untuk namespace URL

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api/fitness-spots/', views.get_fitness_spots_data, name='get_fitness_spots_data'),
    path('api/map-boundaries/', views.get_map_boundaries, name='get_map_boundaries'),
]
