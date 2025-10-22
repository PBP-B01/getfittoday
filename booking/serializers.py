from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Resource
from .services import create_booking

class BookingCreateSerializer(serializers.Serializer):
    resource_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()

    def validate(self, data):
        Resource.objects.get(pk=data["resource_id"], is_active=True)

        if data["end_time"] <= data["start_time"]:
            raise serializers.ValidationError("Durasi tidak valid.")
        if data["start_time"] <= timezone.now():
            raise serializers.ValidationError("Waktu mulai sudah lewat, pilih waktu lain.")
        return data

    def create(self, validated):
        user = self.context["request"].user
        res = Resource.objects.get(pk=validated["resource_id"])
        minutes = int((validated["end_time"] - validated["start_time"]).total_seconds() // 60)
        price = (res.price_per_hour / Decimal(60)) * Decimal(minutes)
        return create_booking(user, res.id, validated["start_time"], validated["end_time"], price)
