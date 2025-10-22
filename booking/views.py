from rest_framework import views, permissions, status
from rest_framework.response import Response
from datetime import datetime, timedelta, time as dtime
from django.utils import timezone
from .models import Resource, Booking, BookingStatus
from .serializers import BookingCreateSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Resource, Booking

@login_required
def booking_page(request):
    return render(request, "booking_form.html")

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
        slots, time = [], start_day
        while time + step <= end_day:
            start, end = time, time + step
            if not any(start < busy_end and end > busy_start for busy_start, busy_end in busy):
                slots.append({"start": start, "end": end})
            time = end
        return Response(slots)

class BookingCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        book = serializer.save()
        return Response({"id": str(book.id), "status": book.status, "price": str(book.price)}, status=status.HTTP_201_CREATED)
