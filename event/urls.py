from django.urls import path
from . import views

<<<<<<< HEAD
urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('create/', views.create_event, name='create_event'),
    path('edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('join/<int:event_id>/', views.join_event, name='join_event'),
    path('leave/<int:event_id>/', views.leave_event, name='leave_event'),
=======
app_name = 'event'

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('ajax/create/', views.create_event, name='create_event'),
    path('ajax/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('ajax/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('ajax/join/<int:event_id>/', views.join_event, name='join_event'),
    path('ajax/leave/<int:event_id>/', views.leave_event, name='leave_event'),
    path('api/community/<int:community_id>/', views.community_events_api, name='community_events_api'),
>>>>>>> master
]