from django.db.models import Q
from rest_framework import views, permissions, status
from rest_framework.response import Response
from datetime import datetime, date, timedelta, time as dtime
from django.utils import timezone
from .models import Resource, Booking, BookingStatus
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Resource, Booking
from home.utils.spots_loader import load_all_spots
from django.db import transaction, IntegrityError
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Case, When, Value, IntegerField, BooleanField
from django.db.models.functions import Coalesce
from uuid import UUID
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

def user_or_admin_required(view_func):
    """
    Decorator: Memerlukan login Django ATAU session admin.
    Jika tidak, redirect ke login.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated or request.session.get('is_admin', False):
            return view_func(request, *args, **kwargs)
        else:
            login_url = reverse('central:login')
            return redirect(f'{login_url}?next={request.path}')
    return _wrapped_view

@user_or_admin_required
def booking_page(request):
    raw = load_all_spots()
    spots = []
    for s in raw:
        if isinstance(s, dict):
            spots.append({
                "place_id": s.get("place_id"),
                "name": s.get("name"),
                "latitude": s.get("latitude"),
                "longitude": s.get("longitude"),
            })
        else:
            spots.append({
                "place_id": getattr(s, "place_id"),
                "name": getattr(s, "name"),
                "latitude": getattr(s, "latitude"),
                "longitude": getattr(s, "longitude"),
            })
    return render(request, "booking_form.html", {"spots": spots})

@user_or_admin_required
def my_bookings_page(request):
    tz = timezone.get_current_timezone()
    now = timezone.now()

    if request.session.get('is_admin', False):
        base_query = Booking.objects.select_related("resource", "user").all()
    else:
        base_query = Booking.objects.filter(user=request.user).select_related("resource")

    base = (
        base_query
        .annotate(
            status_prio=Case(
                When(status=BookingStatus.PENDING, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("status_prio", "-start_time")
    )

    items = []
    for b in base:
        place = (
            getattr(b.resource, "name", None)
            or getattr(b.resource, "location_name", None)
            or getattr(b.resource, "place_id", "")
        )

        user_info = ""
        if request.session.get('is_admin', False) and hasattr(b, 'user') and b.user:
            user_info = f" ({b.user.username})"

        items.append({
            "id": str(b.id),
            "place_name": place + user_info,
            "start": to_local(b.start_time, tz),
            "end": to_local(b.end_time, tz),
            "status": b.status,
            "can_cancel": b.start_time > now and b.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED],
        })

    return render(request, "my_bookings.html", {"items": items})


def to_local(dt, tz):
    if not dt:
        return dt
    return timezone.localtime(dt, tz) if timezone.is_aware(dt) else timezone.make_aware(dt, tz)

def _resolve_resource(rid: str | None, label: str | None):
    qs = Resource.objects.all()
    res = None
    if rid:
        try:
            UUID(str(rid))
            res = qs.filter(pk=rid).first()
        except Exception:
            pass

    if not res and rid and hasattr(Resource, "place_id"):
        res = qs.filter(place_id=rid).first()

    if not res and rid:
        res = qs.filter(Q(location_name__iexact=rid) | Q(name__iexact=rid)).first()
    if not res and label:
        res = qs.filter(Q(location_name__iexact=label) | Q(name__iexact=label)).first()

    return res

class AvailabilityView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        rid = request.query_params.get("resource")
        label = (request.query_params.get("label") or "").strip()
        date_str = request.query_params.get("date")
        if not rid or not date_str:
            return Response({"detail": "missing resource/date"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            d = date.fromisoformat(date_str)
        except Exception:
            return Response({"detail": "bad date"}, status=status.HTTP_400_BAD_REQUEST)

        tz = timezone.get_current_timezone()
        open_start = timezone.make_aware(datetime.combine(d, dtime(10, 0)), tz)
        open_end   = timezone.make_aware(datetime.combine(d, dtime(20, 0)), tz)

        res = _resolve_resource(rid, label)

        busy = []
        if res:
            qs = (Booking.objects
                .filter(resource=res,
                        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
                        start_time__lt=open_end,
                        end_time__gt=open_start)
                .values("start_time", "end_time"))

            for b in qs:
                s = to_tz(b["start_time"], tz)
                e = to_tz(b["end_time"], tz)
                if e > open_start and s < open_end:
                    busy.append({"start": max(s, open_start), "end": min(e, open_end)})
        free = [(open_start, open_end)]
        for b in sorted(busy, key=lambda x: x["start"]):
            new_free = []
            for f_start, f_end in free:
                if b["end"] <= f_start or b["start"] >= f_end:
                    new_free.append((f_start, f_end))
                else:
                    if b["start"] > f_start:
                        new_free.append((f_start, b["start"]))
                    if b["end"] < f_end:
                        new_free.append((b["end"], f_end))
            free = new_free

        step = timedelta(minutes=15)
        slots = []
        for f_start, f_end in free:
            t = f_start
            while t + step <= f_end:
                slots.append({"start": t.isoformat(), "end": (t + step).isoformat()})
                t += step

        return Response(slots, status=200)

def to_tz(dt, tz):
    if dt is None:
        return None
    return timezone.localtime(dt, tz) if timezone.is_aware(dt) else timezone.make_aware(dt, tz)

def _parse_iso(s: str):
    try:
        dt = datetime.fromisoformat((s or '').replace('Z', '+00:00'))
    except Exception:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return dt

class BookingCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data   = request.data or {}
        rid    = data.get("resource_id")
        label  = (data.get("resource_label") or "").strip()
        start  = _parse_iso(data.get("start_time"))
        end    = _parse_iso(data.get("end_time"))

        if not (start and end) or end <= start:
            return Response({"detail": "bad datetime"}, status=400)

        res = _resolve_resource(rid, label)

        if not res and label:
            r_kwargs = {
                "name": label,
                "location_name": label,
                "is_active": True,
            }
            if hasattr(Resource, "place_id") and rid:
                r_kwargs["place_id"] = rid
            if hasattr(Resource, "slot_minutes"):
                r_kwargs["slot_minutes"] = 60
            if hasattr(Resource, "price_per_hour"):
                r_kwargs["price_per_hour"] = 0
            if hasattr(Resource, "sport_type"):
                r_kwargs["sport_type"] = "other"
            try:
                res = Resource.objects.create(**r_kwargs)
            except Exception as e:
                return Response({"detail": "resource create failed"}, status=400)

        if not res:
            return Response({"detail": "resource not found"}, status=400)

        clash = Booking.objects.filter(
            resource=res,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
            start_time__lt=end,
            end_time__gt=start,
        ).exists()
        if clash:
            return Response({"detail": "time conflict"}, status=409)

        def has_bfield(name):
            return any(getattr(f, "name", None) == name for f in Booking._meta.get_fields())

        b_kwargs = dict(
            user=request.user,
            resource=res,
            start_time=start,
            end_time=end,
            status=BookingStatus.PENDING,
        )

        if has_bfield("price"):
            dur_hours = Decimal((end - start).total_seconds()) / Decimal(3600)
            price_per_hour = Decimal(getattr(res, "price_per_hour", 0) or 0)
            b_kwargs["price"] = (price_per_hour * dur_hours).quantize(Decimal("0.01"))

        try:
            with transaction.atomic():
                b = Booking.objects.create(**b_kwargs)
        except IntegrityError as e:
            return Response({"detail": f"integrity error: {e}"}, status=400)
        except Exception as e:
            return Response({"detail": f"failed: {e.__class__.__name__}"}, status=400)

        return Response({"id": str(b.id)}, status=201)

    
class MyBookingAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = (Booking.objects
              .filter(user=request.user)
              .select_related("resource")
              .order_by("-start_time"))
        out = []
        for b in qs:
            out.append({
                "id": str(b.id),
                "place_name": getattr(b.resource, "name", "") or getattr(b.resource, "place_id", ""),
                "start": timezone.localtime(b.start_time).isoformat(),
                "end": timezone.localtime(b.end_time).isoformat(),
                "status": b.status,
            })
        return Response(out, status=200)

class BookingCancelView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        b = get_object_or_404(Booking, pk=pk, user=request.user)
        if b.start_time > timezone.now() and b.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            b.status = BookingStatus.CANCELLED
            b.save(update_fields=["status"])

        if "text/html" in request.META.get("HTTP_ACCEPT", ""):
            return redirect("booking:mine_page")

        return Response({"status": b.status}, status=200)