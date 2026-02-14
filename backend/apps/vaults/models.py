import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RoleChoices(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    CONTRIBUTOR = 'CONTRIBUTOR', 'Contributor'
    VIEWER = 'VIEWER', 'Viewer'


ROLE_WEIGHTS = {
    RoleChoices.OWNER: 3,
    RoleChoices.CONTRIBUTOR: 2,
    RoleChoices.VIEWER: 1,
}


class Vault(models.Model):
    """
    Knowledge Vault - shared repository for research sources and citations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_vaults'
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vaults'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_archived']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name
