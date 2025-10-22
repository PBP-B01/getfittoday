from django.urls import path
from .views import AvailabilityView, BookingCreateView, booking_page, booking_form, booking_submit

app_name = "booking"

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
    path("book/", BookingCreateView.as_view(), name="book"),
    path("page/", booking_page, name="booking_page"),
    path("form/", booking_form, name="booking_form"),
    path("submit/", booking_submit, name="booking_submit"),
]
