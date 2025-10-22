from django.db import transaction
from django.utils import timezone
from .models import Booking, BookingStatus, Resource

@transaction.atomic
def create_booking(user, resource_id, start, end, price):
    res = Resource.objects.select_for_update().get(pk=resource_id, is_active=True)
    if end <= start:
        raise ValueError("Range waktu tidak valid.")
    if start <= timezone.now():
        raise ValueError("Waktu mulai sudah lewat, pilih waktu lain.")

    conflict = Booking.objects.select_for_update().filter(
        resource=res,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        start_time__lt=end,
        end_time__gt=start,
    ).exists()
    if conflict:
        raise ValueError("Slot sudah terisi.")

    return Booking.objects.create(
        user=user, resource=res, start_time=start, end_time=end,
        price=price, status=BookingStatus.CONFIRMED
    )
