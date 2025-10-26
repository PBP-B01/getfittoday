from django.urls import path, include
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api/fitness-spots/', views.get_fitness_spots_data, name='get_fitness_spots_data_api'),
    path('api/map-boundaries/', views.get_map_boundaries, name='get_map_boundaries'),
    path('community/by-place/<str:place_id>/', views.communities_by_place, name='communities_by_place')
]
