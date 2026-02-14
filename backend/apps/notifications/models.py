from __future__ import annotations

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    emailed_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
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

    def mark_as_read(self) -> None:
        """Mark notification as read with current timestamp."""
        from django.utils import timezone
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])


class NotificationPreferences(models.Model):
    """User preferences for notification delivery"""

    DIGEST_FREQUENCY_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('none', 'No Emails'),
    ]

    user: models.OneToOneField = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Email preferences
    email_vault_activity: models.BooleanField = models.BooleanField(default=True)
    email_mentions: models.BooleanField = models.BooleanField(default=True)
    email_digest_frequency: models.CharField = models.CharField(
        max_length=20,
        choices=DIGEST_FREQUENCY_CHOICES,
        default='daily'
    )

    # Push notification preferences
    push_enabled: models.BooleanField = models.BooleanField(default=True)
    push_sources: models.BooleanField = models.BooleanField(default=True)
    push_annotations: models.BooleanField = models.BooleanField(default=True)

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} notification preferences"  # type: ignore[attr-defined]


class MutedVault(models.Model):
    """Tracks which vaults a user has muted to suppress notifications"""

    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='muted_vaults'
    )
    vault: models.ForeignKey = models.ForeignKey(
        'vaults.Vault',
        on_delete=models.CASCADE,
        related_name='muted_by_users'
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'vault']]
        indexes = [
            models.Index(fields=['user', 'vault']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} muted {self.vault.name}"  # type: ignore[attr-defined]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_notification_preferences(sender, instance, created, **kwargs) -> None:  # type: ignore[misc]
    """Auto-create notification preferences when user is created"""
    del sender, kwargs  # Unused but required by signal
    if created:
        NotificationPreferences.objects.create(user=instance)
