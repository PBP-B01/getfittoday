from django.urls import path
from . import views
from community.views import (
    delete_community, promote_admin, # Import views baru
)

urlpatterns = [
    # --- URL untuk Web (HTML/AJAX) ---
    path('', views.community_list, name='community_list'),
    path('list/', views.community_list, name='community_list'),
    path('add/', views.add_community, name='add_community'),
    path('detail/<int:pk>/', views.community_detail, name='community_detail'),
    path('ajax/add/', views.ajax_add_community, name='ajax_add_community'),
    path('ajax/edit/<int:community_id>/', views.ajax_edit_community, name='ajax_edit_community'),
    path('ajax/delete/<int:community_id>/', views.ajax_delete_community, name='ajax_delete_community'),
    path('ajax/add_admin/<int:community_id>/', views.ajax_add_community_admin, name='ajax_add_community_admin'),
    path('ajax/join/<int:community_id>/', views.ajax_join_community, name='ajax_join_community'),
    path('ajax/leave/<int:community_id>/', views.ajax_leave_community, name='ajax_leave_community'),
    path('by-place-json/<str:place_id>/', views.communities_by_place_json, name='communities_by_place_json'),

    # --- API JSON untuk Flutter (PENTING!) ---
    path('api/featured/', views.featured_communities_api, name='featured_communities_api'),
    path('api/communities/', views.communities_json, name='communities_json'), # List Community
    path('api/community/<int:pk>/', views.community_detail_json, name='community_detail_json'), # Detail Community
    path('api/create/', views.create_community_flutter, name='create_community_flutter'), # Create Community
    path('api/edit/<int:community_id>/', views.edit_community_flutter, name='edit_community_flutter'), # Edit Community
    path('api/fitness-spots/', views.get_fitness_spots_json, name='get_fitness_spots_json'), # Dropdown Lokasi
    path('api/delete/<int:community_id>/', delete_community, name='delete_community_api'),
    path('api/promote/<int:community_id>/', promote_admin, name='promote_admin_api'),
]