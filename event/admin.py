from django.contrib import admin
<<<<<<< HEAD

# Register your models here.
=======
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'community', 
        'date', 
        'location', 
        'created_by', 
        'participant_count', 
        'registration_status',
        'created_at'
    )
    list_filter = ('community', 'date', 'created_at')
    search_fields = ('name', 'description', 'location', 'community__name', 'created_by__username')
    date_hierarchy = 'date'
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at', 'updated_at', 'participant_count')
    
    fieldsets = (
        ('Event Information', {
            'fields': ('name', 'description', 'community', 'created_by')
        }),
        ('Date & Location', {
            'fields': ('date', 'location', 'registration_deadline')
        }),
        ('Participants', {
            'fields': ('participants', 'participant_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def participant_count(self, obj):
        """Display number of participants"""
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def registration_status(self, obj):
        """Display registration status with color indicator"""
        return obj.registration_open()
    registration_status.short_description = 'Registration Open'
    registration_status.boolean = True
>>>>>>> master
