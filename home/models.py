from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

class PlaceType(models.Model):
    """
    Model untuk menyimpan kategori atau jenis tempat yang unik.
    Contoh: 'gym', 'stadium', 'swimming_pool'.
    """
    name = models.CharField(
        max_length=100, 
        primary_key=True, 
        unique=True,
        help_text="Nama jenis tempat dari Google API (misalnya, 'gym')"
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Jenis Tempat"
        verbose_name_plural = "Jenis-Jenis Tempat"

class FitnessSpot(models.Model):
    """
    Model Django untuk menyimpan informasi tentang tempat kebugaran
    yang diambil dari Google Places API.
    """
    place_id = models.CharField(
        max_length=255, 
        primary_key=True, 
        unique=True,
        help_text="ID unik dari Google Places API"
    )

    name = models.CharField(
        max_length=255,
        help_text="Nama tampilan tempat"
    )

    types = models.ManyToManyField(
        PlaceType,
        blank=True,
        help_text="Kategori tempat dari Google"
    )

    address = models.TextField(
        help_text="Alamat lengkap yang diformat"
    )

    phone_number = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Nomor telepon nasional"
    )

    website = models.URLField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="URL situs web resmi"
    )

    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        help_text="Koordinat Lintang (Latitude)"
    )
    
    longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        help_text="Koordinat Bujur (Longitude)"
    )

    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        null=True, 
        blank=True,
        help_text="Rating rata-rata tempat (1.0 - 5.0)"
    )

    rating_count = models.PositiveIntegerField(
        default=0,
        help_text="Jumlah total ulasan pengguna"
    )

    class Meta:
        ordering = ['-rating_count', 'name']
        verbose_name = "Tempat Kebugaran"
        verbose_name_plural = "Tempat Kebugaran"

    def __str__(self):
        return self.name

#berjalan setiap kali sebuah objek PlaceType akan dihapus.
@receiver(pre_delete, sender=PlaceType)
def delete_related_fitness_spots(sender, instance, **kwargs):
    """
    Sinyal ini akan berjalan SEBELUM sebuah objek PlaceType dihapus.
    Ini akan menghapus semua FitnessSpot yang terkait dengannya.
    """
    instance.fitnessspot_set.all().delete()

