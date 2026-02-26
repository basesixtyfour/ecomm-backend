from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, User
from .tasks import send_welcome_email


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        send_welcome_email.delay(
            str(instance.id),
            instance.email,
            instance.username,
        )