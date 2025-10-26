
from django.db import models
from django.conf import settings


class CommunityCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Kategori Komunitas"
        verbose_name_plural = "Kategori Komunitas"

    def __str__(self):
        return self.name

class Community(models.Model):
    name = models.CharField(max_length=200, help_text='Nama komunitas olahraga')
    description = models.TextField(help_text='Deskripsi singkat komunitas')
    contact_info = models.CharField(max_length=255, blank=True, help_text='Kontak admin komunitas (bisa berupa Instagram, nomor WA, dll)')
    created_at = models.DateTimeField(auto_now_add=True)
    fitness_spot = models.ForeignKey(
        'home.FitnessSpot',
        on_delete=models.deletion.CASCADE,
        related_name='communities',
        help_text='Tempat kebugaran tempat komunitas ini sering berlatih'
    )
    category = models.ForeignKey(
        CommunityCategory,
        on_delete=models.deletion.CASCADE,
        related_name='communities',
        null=True,
        blank=True,
        help_text='Kategori komunitas (misalnya: gym, futsal, yoga)'
    )
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='managed_communities'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='joined_communities'
    )

    class Meta:
        verbose_name = 'Komunitas'
        verbose_name_plural = 'Komunitas'
        ordering = ['-created_at'] 

    def __str__(self):
        return self.name

    def is_admin(self, user):
        """Check if user is admin of this community"""
        if not user.is_authenticated:
            return False
        return self.admins.filter(id=user.id).exists()
    
    def is_member(self, user):
        """Check if user is member of this community"""
        if not user.is_authenticated:
            return False
        return self.members.filter(id=user.id).exists()

class CommunityPost(models.Model):
    community = models.ForeignKey(Community, on_delete=models.deletion.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} (in {self.community.name})'