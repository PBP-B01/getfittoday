from django.urls import path
from . import views

app_name = 'event'

urlpatterns = [
    path('api/create/', views.create_event_flutter, name='create_event_flutter'),
    path('', views.event_list, name='event_list'),
    path('ajax/create/', views.create_event, name='create_event'),
    path('ajax/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('ajax/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('ajax/join/<int:event_id>/', views.join_event, name='join_event'),
    path('ajax/leave/<int:event_id>/', views.leave_event, name='leave_event'),
    path('ajax/get/<int:event_id>/', views.get_event_detail, name='get_event_detail'),
    path('api/community/<int:community_id>/', views.community_events_api, name='community_events_api'),
    path('api/my-admin-communities/', views.get_user_admin_communities, name='get_user_admin_communities'),
    path('api/list/', views.show_event_api, name='show_event_api'),
    path('api/join/<int:event_id>/', views.join_event_flutter, name='join_event_flutter'),
    path('api/leave/<int:event_id>/', views.leave_event_flutter, name='leave_event_flutter'),
    path('api/edit/<int:event_id>/', views.edit_event_flutter, name='edit_event_flutter'),
    path('api/delete/<int:event_id>/', views.delete_event_flutter, name='delete_event_flutter'),
]