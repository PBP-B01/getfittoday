from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include(("home.urls", "home"), namespace="home")),
    path("booking/", include(("booking.urls", "booking"), namespace="booking")),
    path("central/", include(("central.urls", "central"), namespace="central")),
<<<<<<< HEAD
    path('store/', include('store.urls')) # app store
=======
    path("blognevent/", include("BlognEvent.urls", namespace="BlogNEvent"))
>>>>>>> 962ade9 (blogs & events w/o styling and filter)
]