from uuid6 import uuid7
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    email = models.EmailField(unique=True, null=False, blank=False)

    class Meta:
        db_table = "auth_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"UserProfile for {self.user.username}"