from django.contrib import admin
from django.contrib import admin
from .models import FitnessSpot, PlaceType

class FitnessSpotAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'rating', 'rating_count')
    search_fields = ('name', 'address')
    list_filter = ('types', 'rating')

class PlaceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(FitnessSpot, FitnessSpotAdmin)
admin.site.register(PlaceType, PlaceTypeAdmin)