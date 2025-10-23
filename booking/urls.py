from django.urls import path
from . import views

app_name = "booking"

urlpatterns = [
    path("page/", views.booking_page, name="page"),
    path("availability/", views.AvailabilityView.as_view(), name="availability"),
    path("book/", views.BookingCreateView.as_view(), name="book"),
    path("mine/", views.my_bookings_page, name="mine_page"),
    path("api/mine/", views.MyBookingAPI.as_view(), name="mine_api"),
    path("cancel/<uuid:pk>/", views.BookingCancelView.as_view(), name="booking-cancel"),
]
