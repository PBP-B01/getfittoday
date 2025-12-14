from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import timedelta
from rest_framework.test import APIClient, APITestCase
from .models import Resource, Booking, BookingStatus
from .services import create_booking
from .serializers import BookingCreateSerializer
from django.test import TestCase
from rest_framework.test import APIClient
from uuid import UUID
from .serializers import BookingCreateSerializer, _is_uuid
from django.contrib.auth import get_user_model

class BookingBaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.user = User.objects.create_user(username="tester", password="12345")
        self.resource = Resource.objects.create(
            name="Lapangan A",
            location_name="Jakarta",
            sport_type="futsal",
            is_active=True,
            slot_minutes=60,
            price_per_hour=Decimal("50000.00")
        )

class BookingModelTests(BookingBaseTest):
    def test_resource_str(self):
        self.assertIn("Jakarta - Lapangan A", str(self.resource))

    def test_booking_creation_and_status(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end,
            price=Decimal("50000.00"),
        )
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(str(booking.resource), "Jakarta - Lapangan A")

class BookingServiceTests(BookingBaseTest):
    def test_create_booking_success(self):
        start = timezone.now() + timedelta(hours=3)
        end = start + timedelta(hours=1)
        booking = create_booking(self.user, self.resource.id, start, end, Decimal("100000.00"))
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)

    def test_create_booking_conflict(self):
        start = timezone.now() + timedelta(hours=3)
        end = start + timedelta(hours=1)
        Booking.objects.create(
            user=self.user, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100000.00"), status=BookingStatus.CONFIRMED
        )
        with self.assertRaises(ValueError):
            create_booking(self.user, self.resource.id, start, end, Decimal("100000.00"))

class BookingSerializerTests(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.user = get_user_model().objects.create_user(
            username="testuser", password="password123"
        )
        self.resource = Resource.objects.create(
            name="Gym Room",
            price_per_hour=100
        )

    def test_serializer_valid_and_create(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        data = {
            "resource_id": str(self.resource.id),
            "start_time": start,
            "end_time": end,
            "price": self.resource.price_per_hour,  
        }
        serializer = BookingCreateSerializer(
            data=data,
            context={"request": type("r", (), {"user": self.user})()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        booking = serializer.save()
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)
        self.assertEqual(booking.price, data["price"])

    def test_invalid_time_raises_error(self):
        start = timezone.now() + timedelta(hours=1)
        end = start - timedelta(hours=1)
        serializer = BookingCreateSerializer(
            data={
                "resource_id": str(self.resource.id),
                "start_time": start,
                "end_time": end,
                "price": self.resource.price_per_hour  
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_missing_price_fills_default(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        data = {
            "resource_id": str(self.resource.id),
            "start_time": start,
            "end_time": end,
        }
        serializer = BookingCreateSerializer(
            data=data,
            context={"request": type("r", (), {"user": self.user})()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        booking = serializer.save()
        self.assertEqual(booking.price, self.resource.price_per_hour)

class BookingViewTests(BookingBaseTest):
    def setUp(self):
        super().setUp()
        self.api_client.login(username="tester", password="12345")

    def test_booking_page_renders(self):
        self.client.login(username="tester", password="12345")
        res = self.client.get(reverse("booking:page"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "booking_form.html")

    def test_my_bookings_page_renders(self):
        self.client.login(username="tester", password="12345")
        res = self.client.get(reverse("booking:mine_page"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "my_bookings.html")

    def test_availability_bad_request(self):
        res = self.api_client.get(reverse("booking:availability"))
        self.assertEqual(res.status_code, 400)

    def test_availability_valid_request(self):
        date_str = (timezone.now().date() + timedelta(days=1)).isoformat()
        res = self.api_client.get(reverse("booking:availability"), {"resource": str(self.resource.id), "date": date_str})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

    def test_booking_create_success(self):
        start = (timezone.now() + timedelta(hours=1)).isoformat()
        end = (timezone.now() + timedelta(hours=2)).isoformat()
        data = {
            "resource_id": str(self.resource.id),
            "start_time": start,
            "end_time": end,
        }
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertIn("id", res.data)

    def test_booking_create_conflict(self):
        now = timezone.now()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)
        Booking.objects.create(
            user=self.user, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100000.00"), status=BookingStatus.CONFIRMED
        )
        data = {
            "resource_id": str(self.resource.id),
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 409)

    def test_my_bookings_api(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        Booking.objects.create(
            user=self.user, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100000.00"), status=BookingStatus.CONFIRMED
        )
        res = self.api_client.get(reverse("booking:mine_api"))
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.data), 1)

    def test_cancel_booking(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        booking = Booking.objects.create(
            user=self.user, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100000.00"), status=BookingStatus.CONFIRMED
        )
        url = reverse("booking:booking-cancel", args=[booking.id])
        res = self.api_client.post(url)
        booking.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(booking.status, BookingStatus.CANCELLED)

class BookingExtraBaseTest(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = type("User", (), {"id": 1, "username": "tester"})()  
        self.resource = Resource.objects.create(
            name="Gym Room",
            location_name="Jakarta",
            sport_type="futsal",
            price_per_hour=Decimal("100.00")
        )

class ResourceModelExtraTests(BookingExtraBaseTest):
    def test_resource_str_no_location(self):
        r = Resource.objects.create(
            name="Lapangan B",
            location_name="",
            sport_type="badminton",
            price_per_hour=Decimal("50.00")
        )
        self.assertEqual(str(r), "Lapangan B")

class BookingSerializerExtraTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="tester_extra", password="12345"
        )
        self.resource = Resource.objects.create(
            name="Gym Room",
            location_name="Jakarta",
            sport_type="futsal",
            price_per_hour=Decimal("100.00")
        )

    def test_serializer_missing_price_uses_resource_default(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        data = {
            "resource_id": str(self.resource.id),
            "start_time": start,
            "end_time": end,
        }
        serializer = BookingCreateSerializer(
            data=data,
            context={"request": type("r", (), {"user": self.user})()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        booking = serializer.save()
        self.assertEqual(booking.price, self.resource.price_per_hour)

    def test_create_serializer_with_invalid_uuid_and_missing_resource(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        data = {
            "resource_id": "not-a-uuid",  
            "resource_label": "External Spot",
            "start_time": start,
            "end_time": end,
        }
        serializer = BookingCreateSerializer(
            data=data,
            context={"request": type("r", (), {"user": self.user})()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        booking = serializer.save()
        self.assertEqual(booking.price, 100)  
        self.assertEqual(booking.resource.name, "External Spot")

class BookingServiceExtraTests(BookingExtraBaseTest):
    def test_create_booking_invalid_range(self):
        start = timezone.now() + timedelta(hours=2)
        end = start - timedelta(hours=1)
        with self.assertRaises(ValueError):
            create_booking(self.user, self.resource.id, start, end, Decimal("100.00"))

    def test_create_booking_start_in_past(self):
        start = timezone.now() - timedelta(hours=1)
        end = timezone.now() + timedelta(hours=1)
        with self.assertRaises(ValueError):
            create_booking(self.user, self.resource.id, start, end, Decimal("100.00"))

class BookingViewsExtraTests(BookingExtraBaseTest):
    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import User
        self.user_obj = User.objects.create_user(username="apiuser", password="12345")
        self.api_client.force_authenticate(user=self.user_obj)

    def test_availability_view_bad_date(self):
        res = self.api_client.get(reverse("booking:availability"), {"resource": str(self.resource.id), "date": "bad-date"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "bad date")

    def test_booking_create_view_clash(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        Booking.objects.create(
            user=self.user_obj, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100.00"), status=BookingStatus.CONFIRMED
        )
        data = {"resource_id": str(self.resource.id), "start_time": start.isoformat(), "end_time": end.isoformat()}
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 409)

    def test_booking_create_view_resource_not_found(self):
        data = {"resource_id": str(UUID(int=0)), "start_time": (timezone.now() + timedelta(hours=1)).isoformat(),
                "end_time": (timezone.now() + timedelta(hours=2)).isoformat()}
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "resource not found")

    def test_booking_create_view_price_computation(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2) 
        data = {"resource_id": str(self.resource.id), "start_time": start.isoformat(), "end_time": end.isoformat()}
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 201)
        booking = Booking.objects.get(pk=res.data["id"])
        self.assertEqual(booking.price, Decimal("200.00"))  
    
    def test_booking_create_view_bad_datetime(self):
        data = {"resource_id": str(self.resource.id), "start_time": "", "end_time": ""}
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "bad datetime")

    def test_booking_cancel_view_cannot_cancel(self):
        past_start = timezone.now() - timedelta(hours=2)
        past_end = past_start + timedelta(hours=1)
        b = Booking.objects.create(
            user=self.user_obj, resource=self.resource,
            start_time=past_start, end_time=past_end,
            price=Decimal("100.00"), status=BookingStatus.CONFIRMED
        )
        url = reverse("booking:booking-cancel", args=[b.id])
        res = self.api_client.post(url)
        b.refresh_from_db()
        self.assertEqual(b.status, BookingStatus.CONFIRMED)
        self.assertEqual(res.status_code, 200)

    def test_availability_view_missing_resource_or_date(self):
        res1 = self.api_client.get(reverse("booking:availability"), {"date": "2025-10-26"})
        self.assertEqual(res1.status_code, 400)
        self.assertEqual(res1.data["detail"], "missing resource/date")
        
        res2 = self.api_client.get(reverse("booking:availability"), {"resource": str(self.resource.id)})
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(res2.data["detail"], "missing resource/date")

class BookingViewsFullCoverageTests(BookingExtraBaseTest):
    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import User
        self.user_obj = User.objects.create_user(username="fullcover", password="12345")
        self.api_client.force_authenticate(user=self.user_obj)

    def test_availability_missing_params(self):
        res = self.api_client.get(reverse("booking:availability"))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "missing resource/date")

    def test_availability_bad_date_format(self):
        res = self.api_client.get(
            reverse("booking:availability"),
            {"resource": str(self.resource.id), "date": "not-a-date"}
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "bad date")

    def test_booking_create_view_resource_not_found_branch(self):
        from uuid import UUID
        data = {
            "resource_id": str(UUID(int=0)),
            "start_time": (timezone.now() + timedelta(hours=1)).isoformat(),
            "end_time": (timezone.now() + timedelta(hours=2)).isoformat(),
        }
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "resource not found")

    def test_booking_create_view_time_conflict_branch(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        Booking.objects.create(
            user=self.user_obj, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100.00"), status=BookingStatus.CONFIRMED
        )
        data = {
            "resource_id": str(self.resource.id),
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 409)

    def test_booking_create_view_exception_branch(self):
        from unittest.mock import patch
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        data = {
            "resource_id": str(self.resource.id),
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }
        with patch("booking.models.Booking.objects.create") as mock_create:
            mock_create.side_effect = Exception("forced error")
            res = self.api_client.post(reverse("booking:book"), data, format="json")
            self.assertEqual(res.status_code, 400)
            self.assertIn("failed", res.data["detail"])

    def test_booking_cancel_cannot_cancel(self):
        past_start = timezone.now() - timedelta(hours=2)
        past_end = timezone.now() - timedelta(hours=1)
        booking = Booking.objects.create(
            user=self.user_obj, resource=self.resource,
            start_time=past_start, end_time=past_end,
            price=Decimal("100.00"), status=BookingStatus.CONFIRMED
        )
        url = reverse("booking:booking-cancel", args=[booking.id])
        res = self.api_client.post(url)
        booking.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)

    def test_parse_iso_with_invalid_string(self):
        from booking.views import _parse_iso
        self.assertIsNone(_parse_iso("invalid-string"))

    def test_to_local_with_naive_datetime(self):
        from booking.views import to_local
        from datetime import datetime
        naive = datetime(2025, 1, 1, 12, 0)
        from django.utils import timezone
        aware = to_local(naive, timezone.get_current_timezone())
        self.assertTrue(timezone.is_aware(aware))

    def test_to_tz_with_none(self):
        from booking.views import to_tz
        self.assertIsNone(to_tz(None, None))

class BookingViewsEdgeCasesTests(BookingExtraBaseTest):
    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import User
        self.user_obj = User.objects.create_user(username="edgeuser", password="12345")
        self.api_client.force_authenticate(user=self.user_obj)

    def test_availability_view_with_busy_slots(self):
        start = timezone.now() + timedelta(hours=11)
        end = start + timedelta(hours=1)
        Booking.objects.create(
            user=self.user_obj,
            resource=self.resource,
            start_time=start,
            end_time=end,
            price=Decimal("50.00"),
            status=BookingStatus.CONFIRMED
        )
        date_str = (start.date()).isoformat()
        res = self.api_client.get(reverse("booking:availability"), {"resource": str(self.resource.id), "date": date_str})
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.data), 0)

    def test_booking_create_view_bad_datetime(self):
        data = {"resource_id": str(self.resource.id), "start_time": "bad", "end_time": "stillbad"}
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "bad datetime")

    def test_booking_create_view_resource_label_branch(self):
        data = {
            "resource_id": "non-existent-uuid",
            "resource_label": "New Spot Label",
            "start_time": (timezone.now() + timedelta(hours=1)).isoformat(),
            "end_time": (timezone.now() + timedelta(hours=2)).isoformat(),
        }
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 201)
        booking = Booking.objects.get(pk=res.data["id"])
        self.assertEqual(booking.resource.name, "New Spot Label")

    def test_booking_create_view_price_none_and_bfield_check(self):
        start = timezone.now() + timedelta(hours=3)
        end = start + timedelta(hours=2)
        resource = Resource.objects.create(name="Zero Price Gym", price_per_hour=0)
        data = {"resource_id": str(resource.id),
                "start_time": start.isoformat(),
                "end_time": end.isoformat()}
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 201)
        booking = Booking.objects.get(pk=res.data["id"])
        self.assertEqual(booking.price, Decimal("0.00"))

    def test_booking_create_view_exception_handling(self):
        data = {"resource_id": str(self.resource.id), "start_time": None, "end_time": None}
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertEqual(res.status_code, 400)

class BookingViewsEdgeCaseTests(BookingExtraBaseTest):
    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import User
        self.user_obj = User.objects.create_user(username="edgeuser", password="12345")
        self.api_client.force_authenticate(user=self.user_obj)

    def test_resolve_resource_invalid_uuid(self):
        from .views import _resolve_resource
        res = _resolve_resource("not-a-uuid", None)
        self.assertIsNone(res)

    def test_resolve_resource_by_label_only(self):
        from .views import _resolve_resource
        r = Resource.objects.create(name="GymX", location_name="Jakarta")
        res = _resolve_resource(None, "GymX")
        self.assertEqual(res, r)

    def test_availability_missing_params(self):
        res = self.api_client.get("/booking/availability/")  
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "missing resource/date")

    def test_availability_no_conflicts(self):
        from datetime import date
        d_str = (timezone.now().date() + timedelta(days=1)).isoformat()
        res = self.api_client.get(reverse("booking:availability"), {"resource": str(self.resource.id), "date": d_str})
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

    def test_booking_create_view_integrity_error(self):
        data = {
            "resource_id": str(self.resource.id),
            "start_time": (timezone.now() + timedelta(hours=1)).isoformat(),
            "end_time": (timezone.now() + timedelta(hours=2)).isoformat()
        }
        from django.db import transaction, IntegrityError
        from .views import BookingCreateView
        view = BookingCreateView.as_view()
        res = self.api_client.post(reverse("booking:book"), data, format="json")
        self.assertIn(res.status_code, [201, 400])  

    def test_booking_cancel_view_html_accept(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        b = Booking.objects.create(
            user=self.user_obj, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100.00"), status=BookingStatus.PENDING
        )
        res = self.api_client.post(reverse("booking:booking-cancel", args=[b.id]),
                                   HTTP_ACCEPT="text/html")
        b.refresh_from_db()
        self.assertEqual(res.status_code, 302)
        self.assertEqual(b.status, BookingStatus.CANCELLED)

    def test_booking_cancel_view_json_accept(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        b = Booking.objects.create(
            user=self.user_obj, resource=self.resource,
            start_time=start, end_time=end,
            price=Decimal("100.00"), status=BookingStatus.PENDING
        )
        res = self.api_client.post(reverse("booking:booking-cancel", args=[b.id]),
                                   HTTP_ACCEPT="application/json")
        b.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], BookingStatus.CANCELLED)

