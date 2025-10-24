from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Community(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_communities')

    def __str__(self):
        return self.name
    
    def is_admin(self, user):
        if not user.is_authenticated:
            return False
        if self.admin == user:
            return True
        return CommunityMember.objects.filter(
            community=self,
            user=user,
            role='admin'
        ).exists()


class CommunityMember(models.Model):
    """
    Model untuk membership komunitas dengan role-based access.
    Untuk support multiple admins di masa depan.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    community = models.ForeignKey(
        Community, 
        on_delete=models.CASCADE, 
        related_name='memberships'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='community_memberships'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['community', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.community.name} ({self.role})"


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
        return self.date <= timezone.now() <= (self.date + timezone.timedelta(hours=2))

    def registration_open(self):
        if hasattr(self, 'registration_deadline') and self.registration_deadline:
            return timezone.now() <= self.registration_deadline
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