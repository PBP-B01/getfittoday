from django.contrib import admin
from .models import Event, Blogs

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'starting_date', 'ending_date', 'event_type_display')

    list_filter = ('starting_date', 'event_type')

    search_fields = ('name', 'description')

    list_display_links = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'user', 'event_type', 'image')
        }),
        ('Date and Location', {
            'fields': ('starting_date', 'ending_date', 'locations')
        }),
    )

    def event_type_display(self, obj):
        if hasattr(obj, 'event_type'):
            return dict(Event.TYPE_EVENTS).get(obj.event_type, obj.event_type)
        return 'N/A'
    event_type_display.short_description = 'Type'

@admin.register(Blogs)
class BlogsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')

    search_fields = ('title', 'body')

    list_display_links = ('title',)

    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'body', 'image')
        }),
    )