from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vault, VaultMembership, AuditLog, RoleChoices


@receiver(post_save, sender=Vault)
def create_owner_membership(sender, instance, created, **kwargs):
    """
    Automatically create OWNER membership for vault creator when vault is created.
    """
    if created:
        VaultMembership.objects.create(
            vault=instance,
            user=instance.owner,
            role=RoleChoices.OWNER,
            added_by=instance.owner
        )


@receiver(post_save, sender=Vault)
def log_vault_mutation(sender, instance, created, **kwargs):
    """
    Log vault creation and updates to audit trail.
    """
    action = 'vault.created' if created else 'vault.updated'
    metadata = {
        'name': instance.name,
        'is_archived': instance.is_archived
    }
    AuditLog.objects.create(
        vault=instance,
        actor=instance.owner,
        action=action,
        metadata=metadata
    )


@receiver(post_save, sender=VaultMembership)
def log_membership_added(sender, instance, created, **kwargs):
    """
    Log when a member is added to a vault.
    """
    if created:
        metadata = {
            'user_id': str(instance.user.id),
            'role': instance.role
        }
        AuditLog.objects.create(
            vault=instance.vault,
            actor=instance.added_by,
            action='membership.added',
            metadata=metadata
        )
