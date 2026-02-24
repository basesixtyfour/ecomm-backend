from django.conf import settings
from django.db import models
from django.utils import timezone


class ChatRoom(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_rooms_as_user",
        db_column="user_id",
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_rooms_as_agent",
        db_column="agent_id",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "chat_rooms"

    def __str__(self):
        return f"ChatRoom {self.id} — {self.user_id} ({self.status})"
