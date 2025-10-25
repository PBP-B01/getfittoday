from django.urls import path, include
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api/map-boundaries/', views.api_map_boundaries, name='api_map_boundaries'),
    path('api/fitness-spots/', views.api_fitness_spots, name='api_fitness_spots'),
    path("central/", include(("central.urls", "central"), namespace="central")),
    path('store/', include('store.urls'))
    path('api/fitness-spots/', views.get_fitness_spots_data, name='get_fitness_spots_data'),
    path('api/map-boundaries/', views.get_map_boundaries, name='get_map_boundaries'),
    path('by-place/<str:place_id>/', views.communities_by_place, name='communities_by_place'),
    path('by-place-json/<str:place_id>/', views.communities_by_place_json, name='communities_by_place_json'),
]
