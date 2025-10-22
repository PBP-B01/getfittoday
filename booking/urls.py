from django.urls import path
from .views import AvailabilityView, BookingCreateView

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
    path("book/", BookingCreateView.as_view(), name="book"),
]
