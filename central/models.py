from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Admin(models.Model):
    name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)

    def set_password(self, raw_password):
        """Meng-hash password sebelum disimpan ke database."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Mengecek apakah password yang dimasukkan sesuai dengan yang di-hash."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name

@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if sender.name == "store":
        if not Admin.objects.filter(name="Agil").exists():
            admin = Admin(name="Agil")
            admin.set_password("Agil123")
            admin.save()
            print("Default admin 'Agil' berhasil dibuat.")
