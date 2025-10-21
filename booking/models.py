import uuid
from django.conf import settings
from django.db import models

class Resource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    location_name = models.CharField(max_length=120, blank=True)
    sport_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    slot_minutes = models.PositiveIntegerField(default=60)
    price_per_hour = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        if self.location_name:
            location = f"{self.location_name} - "
        else:
            location = ""
        return f"{location}{self.name}"

class BookingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name="bookings")
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
