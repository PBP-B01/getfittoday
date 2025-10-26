from django.db import models
from django.conf import settings
from django.utils import timezone
from community.models import Community


class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    
    community = models.ForeignKey(
        Community, 
        on_delete=models.CASCADE, 
        related_name='events'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_events'
    )
    
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='joined_events', 
        blank=True
    )

    registration_deadline = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Batas waktu pendaftaran (opsional)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"{self.name} ({self.community.name})"
    
    def is_past(self):
        return timezone.now() > self.date

    def is_ongoing(self):
        now = timezone.now()
        return self.date <= now <= (self.date + timezone.timedelta(hours=2))
    
    def registration_open(self):
        now = timezone.now()

        if self.registration_deadline:
            return now <= self.registration_deadline

        return not self.is_past()
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        if self.community.is_admin(user):
            return True
        
        return False

    def can_delete(self, user):
        return self.can_edit(user)
    
    def can_join(self, user):
        if not user.is_authenticated:
            return False

        if self.participants.filter(id=user.id).exists():
            return False

        if not self.registration_open():
            return False
        
        return True
    
    def user_is_participant(self, user):
        if not user.is_authenticated:
            return False
        return self.participants.filter(id=user.id).exists()
    
    def participant_count(self):
        return self.participants.count()