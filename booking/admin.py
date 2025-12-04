from django.contrib import admin
from .models import Resource, Booking


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_name', 'sport_type', 'is_active', 'price_per_hour', 'slot_minutes')
    list_filter = ('sport_type', 'is_active')
    search_fields = ('name', 'location_name')
    list_editable = ('is_active', 'price_per_hour', 'slot_minutes')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'resource', 'start_time', 'end_time', 'status', 'price', 'created_at')
    list_filter = ('status', 'resource__sport_type', 'user', 'created_at')
    search_fields = ('user__username', 'resource__name', 'notes')
    list_editable = ('status',)
    date_hierarchy = 'start_time'