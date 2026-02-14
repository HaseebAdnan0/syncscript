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
    default_citation_format = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('apa7', 'APA 7th Edition'),
            ('mla9', 'MLA 9th Edition'),
            ('chicago17', 'Chicago 17th Edition'),
            ('bibtex', 'BibTeX'),
            ('ieee', 'IEEE'),
            ('harvard', 'Harvard'),
        ],
        help_text='Default citation format for this vault (overrides user preference)'
    )
    ai_insights_cache = models.JSONField(
        null=True,
        blank=True,
        help_text='AI-generated vault insights: {themes[], research_gaps[], cross_references[], suggested_searches[], generated_at}'
    )
    ai_insights_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp of last AI insights generation'
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(
        User,
        through='VaultMembership',
        through_fields=('vault', 'user'),
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
    last_accessed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when user last accessed this vault'
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


class AuditLog(models.Model):
    """
    Immutable audit log for research integrity tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vault = models.ForeignKey(
        Vault,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions'
    )
    action = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vault', '-created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.action} on {self.vault.name} at {self.created_at}"
