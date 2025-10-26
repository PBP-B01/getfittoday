# community/urls.py
# community/urls.py
from django.urls import path
from . import views
from django.urls import path, include

app_name = "community"

urlpatterns = [
    path('', views.community_list, name='community_list'),
    path('detail/<int:pk>/', views.community_detail, name='community_detail'),
    path('ajax/add/', views.ajax_add_community, name='ajax_add_community'),
    path('ajax/edit/<int:community_id>/', views.ajax_edit_community, name='ajax_edit_community'),
    path('ajax/delete/<int:community_id>/', views.ajax_delete_community, name='ajax_delete_community'),
    path('ajax/add_admin/<int:community_id>/', views.ajax_add_community_admin, name='ajax_add_community_admin'),
    path('ajax/join/<int:community_id>/', views.ajax_join_community, name='ajax_join_community'),
    path('ajax/leave/<int:community_id>/', views.ajax_leave_community, name='ajax_leave_community'),
    path('by-place-json/<str:place_id>/', views.communities_by_place_json, name='communities_by_place_json'), 
    path('api/featured/', views.featured_communities_api, name='featured_communities_api'),

]