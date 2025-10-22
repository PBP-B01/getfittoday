from rest_framework import views, permissions, status
from rest_framework.response import Response
from datetime import datetime, timedelta, time as dtime
from django.utils import timezone
from .models import Resource, Booking, BookingStatus
from .serializers import BookingCreateSerializer

class AvailabilityView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        resource_id = request.query_params["resource"]
        date_str = request.query_params["date"]
        res = Resource.objects.get(pk=resource_id, is_active=True)

        tz = timezone.get_current_timezone()
        day = datetime.fromisoformat(date_str).date()
        start_day = timezone.make_aware(datetime.combine(day, dtime.min), tz)
        end_day = start_day + timedelta(days=1)

        existing = Booking.objects.filter(
            resource=res,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
            start_time__lt=end_day, end_time__gt=start_day
        ).values("start_time","end_time")
        busy = [(b["start_time"], b["end_time"]) for b in existing]

        step = timedelta(minutes=res.slot_minutes)
        slots, t = [], start_day
        while t + step <= end_day:
            s, e = t, t + step
            if not any(s < be and e > bs for bs, be in busy):
                slots.append({"start": s, "end": e})
            t = e
        return Response(slots)

class BookingCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        ser = BookingCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        b = ser.save()
        return Response({"id": str(b.id), "status": b.status, "price": str(b.price)}, status=status.HTTP_201_CREATED)
