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
    members = models.ManyToManyField(
        User,
        through='VaultMembership',
        related_name='vaults'
    )

    class Meta:
        db_table = 'vaults'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_archived']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name


class VaultMembership(models.Model):
    """
    Through model for vault members with role-based access.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vault = models.ForeignKey(
        Vault,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vault_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.CONTRIBUTOR
    )
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='memberships_created'
    )

    class Meta:
        db_table = 'vault_memberships'
        unique_together = [['vault', 'user']]
        indexes = [
            models.Index(fields=['vault', 'role']),
            models.Index(fields=['user']),
        ]

    def get_role_weight(self):
        """
        Returns the numeric weight for this membership's role.
        """
        return ROLE_WEIGHTS.get(self.role, 0)

    def __str__(self):
        return f"{self.user.username} - {self.vault.name} ({self.role})"
