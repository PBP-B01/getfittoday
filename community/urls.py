from django.urls import path
from . import views


urlpatterns = [
    path('', views.community_list, name='community_list'),  # landing page
    path('add/', views.add_community, name='add_community'), # nanti untuk admin
    # path('category/<slug:slug>/', views.community_by_category, name='community_by_category'),
    # path('<int:pk>/', views.community_detail, name='community_detail'),
    path('list/', views.community_list, name='community_list'),
    path('api/communities/<str:spot_id>/', views.communities_by_spot, name='communities_by_spot'),
    path('by-place-json/<str:place_id>/', views.communities_by_place_json, name='communities_by_place_json'),
    path('admin/', views.admin_community_page, name='admin_community_page'),
    path('ajax/add/', views.ajax_add_community, name='ajax_add_community'),
    path('ajax/edit/<int:community_id>/', views.ajax_edit_community, name='ajax_edit_community'),
    path('ajax/delete/<int:community_id>/', views.ajax_delete_community, name='ajax_delete_community'),
    path('detail/<int:pk>/', views.community_detail, name='community_detail'),
]
