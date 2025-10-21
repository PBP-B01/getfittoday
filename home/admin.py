from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import FitnessSpot, PlaceType

# Sesuaikan tampilan admin untuk FitnessSpot
class FitnessSpotAdmin(admin.ModelAdmin):
    # Kolom yang akan ditampilkan di halaman daftar
    list_display = ('name', 'address', 'rating', 'rating_count')
    # Kolom yang dapat digunakan untuk mencari
    search_fields = ('name', 'address')
    # Filter yang akan muncul di sidebar kanan
    list_filter = ('types', 'rating')

# Sesuaikan tampilan admin untuk PlaceType
class PlaceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Daftarkan model ke situs admin Django
admin.site.register(FitnessSpot, FitnessSpotAdmin)
admin.site.register(PlaceType, PlaceTypeAdmin)