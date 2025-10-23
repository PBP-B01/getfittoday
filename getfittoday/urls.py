from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include(("home.urls", "home"), namespace="home")),
    path("booking/", include(("booking.urls", "booking"), namespace="booking")),
    path("central/", include(("central.urls", "central"), namespace="central")),
    path('store/', include('store.urls')), # app store
    path('community/', include('community.urls')),
    path("central/", include(("central.urls", "central"), namespace="central")),
    path("blognevent/", include("BlognEvent.urls", namespace="BlognEvent"))
]