from django.urls import path
from .views import AvailabilityView, BookingCreateView, booking_page

app_name = "booking"

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
    path("book/", BookingCreateView.as_view(), name="book"),
    path("page/", booking_page, name="booking_page"),
]