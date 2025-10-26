<<<<<<< HEAD
from django.db import models
from django.conf import settings
from django.utils import timezone
=======

from django.db import models
from django.conf import settings
>>>>>>> master


class CommunityCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Kategori Komunitas"
        verbose_name_plural = "Kategori Komunitas"

    def __str__(self):
        return self.name

<<<<<<< HEAD

class Community(models.Model):
    name = models.CharField(max_length=200, help_text='Nama komunitas olahraga')
    description = models.TextField(help_text='Deskripsi singkat komunitas')
    contact_info = models.CharField(max_length=255, blank=True, help_text='Kontak admin komunitas')
    created_at = models.DateTimeField(auto_now_add=True)
    
    fitness_spot = models.ForeignKey(
        'home.FitnessSpot',
        on_delete=models.CASCADE,
        related_name='communities',
        help_text='Tempat kebugaran tempat komunitas ini sering berlatih'
    )
    
    category = models.ForeignKey(
        CommunityCategory,
        on_delete=models.SET_NULL,
        related_name='communities',
        null=True,
        blank=True,
        help_text='Kategori komunitas'
    )

    founder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='founded_communities',
        help_text='Pembuat dan pemilik utama komunitas'
    )

    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='managed_communities',
        help_text='Admin yang bisa mengelola komunitas'
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        # through='CommunityMembership',
        related_name='joined_communities',
        help_text='Anggota komunitas'
=======
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
>>>>>>> master
    )

    class Meta:
        verbose_name = 'Komunitas'
        verbose_name_plural = 'Komunitas'
        ordering = ['-created_at'] 

    def __str__(self):
        return self.name
<<<<<<< HEAD
    
    def is_founder(self, user):
        return self.founder == user
    
    def is_admin(self, user):
        if not user.is_authenticated:
            return False

        if self.is_founder(user):
            return True

        return self.admins.filter(id=user.id).exists()
    
    def is_member(self, user):
        if not user.is_authenticated:
            return False
        return self.members.filter(id=user.id).exists()
    
    def can_manage_admins(self, user):
        if not user.is_authenticated:
            return False
        return self.is_founder(user) or user.is_staff or user.is_superuser
    
    def can_leave(self, user):
        if not user.is_authenticated:
            return False

        if not self.is_admin(user):
            return True

        if self.is_founder(user):
            other_admins_count = self.admins.exclude(id=user.id).count()
            return other_admins_count > 0

        return True


class CommunityMembership(models.Model):
    """
    Through model untuk tracking membership dengan metadata tambahan
    """
    community = models.ForeignKey(
        Community, 
        on_delete=models.CASCADE, 
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='community_memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['community', 'user']
        ordering = ['-joined_at']
        verbose_name = 'Keanggotaan Komunitas'
        verbose_name_plural = 'Keanggotaan Komunitas'

    def __str__(self):
        return f"{self.user.username} - {self.community.name}"


class CommunityPost(models.Model):
    community = models.ForeignKey(
        Community, 
        on_delete=models.CASCADE, 
        related_name='posts'
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts'
    )
=======

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
>>>>>>> master

    def __str__(self):
        return f'{self.title} (in {self.community.name})'