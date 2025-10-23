from django.db import models
from django.conf import settings
import uuid

class Event(models.Model):
    TYPE_EVENTS = [
        ('beginner-friendly', 'Beginner-Friendly'),
        ('competition', 'Competition'),
        ('invite-only', 'Invite-Only'),
        ('Training', 'Training'),
        ('Open House', 'Open House'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="creator_event")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    image = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    starting_date = models.DateTimeField(db_index=True)
    ending_date = models.DateTimeField(db_index=True)
    locations= models.ManyToManyField(
        'home.FitnessSpot',  
        related_name='events',
        blank=True
    )
    def __str__(self):
        return self.name

class Blogs (models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="author_blog")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title =models.CharField(max_length=100)
    image = models.URLField(blank=True, null=True)
    body = models.TextField(blank=True)
    def __str__(self):
        return self.title

