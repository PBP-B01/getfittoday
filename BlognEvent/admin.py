from django.contrib import admin
from .models import Event, Blogs

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'starting_date', 'ending_date') 
    list_filter = ('starting_date',) 
    search_fields = ('name', 'description')
    list_display_links = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'user', 'image') 
        }),
        ('Date and Location', {
            'fields': ('starting_date', 'ending_date', 'locations')
        }),
    )

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