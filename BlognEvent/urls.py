from django.urls import path
from BlognEvent.views import (
    create_event, 
    create_blog, 
    blogevent_page,
    event_form_page,
    blog_form_page,
    event_detail_api,
    blog_detail_api,
)

app_name = 'BlogNEvent'

urlpatterns = [
    path('', blogevent_page, name='blogevent_page'),
    path('event/new/', event_form_page, name='event_form_page'),
    path('event/create/', create_event, name='create_event'),
    path('blog/new/', blog_form_page, name='blog_form_page'),
    path('blog/create/', create_blog, name='create_blog'),
    path('event/<uuid:event_id>/', event_detail_api, name='event_detail_api'),
    path('blog/<uuid:blog_id>/', blog_detail_api, name='blog_detail_api'),
]