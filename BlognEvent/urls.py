from django.urls import path
from BlognEvent import views

app_name = 'BlognEvent'

urlpatterns = [
    path('', views.blogevent_page, name='blogevent_page'),
    path('event/form/', views.event_form_page, name='event_form_page'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/<uuid:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<uuid:event_id>/delete/', views.delete_event, name='delete_event'),
    path('event/<uuid:event_id>/', views.event_detail_api, name='event_detail_api'),
    path('blog/form/', views.blog_form_page, name='blog_form_page'),
    path('blog/create/', views.create_blog, name='create_blog'),
    path('blog/<uuid:blog_id>/edit/', views.edit_blog, name='edit_blog'),  # Changed to uuid
    path('blog/<uuid:blog_id>/delete/', views.delete_blog, name='delete_blog'),  # Changed to uuid
    path('blog/<uuid:blog_id>/', views.blog_detail_api, name='blog_detail_api'),  # Changed to uuid
]