from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """
    Immutable audit log for tracking changes to objects in the system.
    Used for research integrity - captures who did what and when.
    """
    action = models.CharField(max_length=100)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    object_type = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    changes = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['object_type', 'object_id']),
        ]

    def __str__(self) -> str:
        return f"{self.action} on {self.object_type} {self.object_id} at {self.timestamp}"
