# booking/serializers.py
from uuid import UUID
from django.utils import timezone
from rest_framework import serializers
from .models import Resource, Booking, BookingStatus

def _is_uuid(v: str) -> bool:
    try:
        UUID(str(v)); return True
    except Exception:
        return False

class BookingCreateSerializer(serializers.Serializer):
    resource_id = serializers.CharField(required=False, allow_blank=True)
    resource_label = serializers.CharField(required=False, allow_blank=True)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()

    def validate(self, attrs):
        start, end = attrs['start_time'], attrs['end_time']
        if end <= start:
            raise serializers.ValidationError('end_time must be after start_time')
        return attrs

    def create(self, validated):
        request = self.context['request']
        user = request.user
        tz = timezone.get_current_timezone()

        rid = validated.get('resource_id') or ''
        label = (validated.get('resource_label') or '').strip() or 'External spot'
        res = None
        if _is_uuid(rid):
            res = Resource.objects.filter(pk=rid).first()

        if res is None:
            res, _ = Resource.objects.get_or_create(
                name=label[:120],
                defaults=dict(
                    location_name=label[:120],
                    is_active=True,
                    slot_minutes=60,
                    sport_type='other',
                )
            )

        start = validated['start_time']
        end = validated['end_time']
        if timezone.is_naive(start): start = timezone.make_aware(start, tz)
        if timezone.is_naive(end):   end   = timezone.make_aware(end, tz)

        return Booking.objects.create(
            user=user,
            resource=res,
            start_time=start,
            end_time=end,
            status=BookingStatus.CONFIRMED,
        )
