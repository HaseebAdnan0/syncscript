from __future__ import annotations

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Stores user notifications for vault activity"""

    TYPE_CHOICES = [
        ('vault_invite', 'Vault Invite'),
        ('member_joined', 'Member Joined'),
        ('source_added', 'Source Added'),
        ('annotation_reply', 'Annotation Reply'),
        ('mention', 'Mention'),
    ]

    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type: models.CharField = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title: models.CharField = models.CharField(max_length=255)
    body: models.TextField = models.TextField()
    data: models.JSONField = models.JSONField(default=dict, blank=True)
    read_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.type} - {self.title}"  # type: ignore[attr-defined]

    @property
    def is_read(self) -> bool:
        return self.read_at is not None
