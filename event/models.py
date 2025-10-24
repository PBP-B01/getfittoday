from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Community(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_communities')

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    participants = models.ManyToManyField(User, related_name='joined_events', blank=True)

    def __str__(self):
        return f"{self.name} ({self.community.name})"
    
    def is_past(self):
        return timezone.now() > self.date

    def is_ongoing(self):
        """Cek apakah event sedang berlangsung (misal ±2 jam dari waktu mulai)."""
        return self.date <= timezone.now() <= (self.date + timezone.timedelta(hours=2))

    def registration_open(self):
        """Cek apakah masa pendaftaran masih buka."""
        if self.registration_deadline:
            return timezone.now() <= self.registration_deadline
        return not self.is_past()