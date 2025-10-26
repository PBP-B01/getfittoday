# community/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.community_list, name='community_list'),
    path('list/', views.community_list, name='community_list'),
    path('add/', views.add_community, name='add_community'),
    path('detail/<int:pk>/', views.community_detail, name='community_detail'),
<<<<<<< HEAD

    path('ajax/add/', views.ajax_add_community, name='ajax_add_community'),
    path('ajax/edit/<int:community_id>/', views.ajax_edit_community, name='ajax_edit_community'),
    path('ajax/delete/<int:community_id>/', views.ajax_delete_community, name='ajax_delete_community'),
    path('ajax/join/<int:community_id>/', views.ajax_join_community, name='ajax_join_community'),
    path('ajax/leave/<int:community_id>/', views.ajax_leave_community, name='ajax_leave_community'),

    path('ajax/add_admin/<int:community_id>/', views.ajax_add_community_admin, name='ajax_add_community_admin'),
    path('ajax/remove_admin/<int:community_id>/', views.ajax_remove_community_admin, name='ajax_remove_community_admin'),

    path('api/communities/<str:spot_id>/', views.communities_by_spot, name='communities_by_spot'),
    path('by-place-json/<str:place_id>/', views.communities_by_place_json, name='communities_by_place_json'),
=======
    path('ajax/add/', views.ajax_add_community, name='ajax_add_community'),
    path('ajax/edit/<int:community_id>/', views.ajax_edit_community, name='ajax_edit_community'),
    path('ajax/delete/<int:community_id>/', views.ajax_delete_community, name='ajax_delete_community'),
    path('ajax/add_admin/<int:community_id>/', views.ajax_add_community_admin, name='ajax_add_community_admin'),
    path('ajax/join/<int:community_id>/', views.ajax_join_community, name='ajax_join_community'),
    path('ajax/leave/<int:community_id>/', views.ajax_leave_community, name='ajax_leave_community'),
    path('api/communities/<str:spot_id>/', views.communities_by_spot, name='communities_by_spot'), 
    path('by-place-json/<str:place_id>/', views.communities_by_place_json, name='communities_by_place_json'), 
    path('api/featured/', views.featured_communities_api, name='featured_communities_api'),

>>>>>>> master
]