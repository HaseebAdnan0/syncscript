import threading
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import Vault, VaultMembership, AuditLog, RoleChoices

# Thread-local storage to track vaults being deleted (cascade delete detection)
_deleting_vaults = threading.local()


def is_vault_being_deleted(vault_id):
    """Check if a vault is currently being deleted (in a cascade delete)."""
    deleting = getattr(_deleting_vaults, 'ids', set())
    return str(vault_id) in deleting


def mark_vault_deleting(vault_id):
    """Mark a vault as being deleted."""
    if not hasattr(_deleting_vaults, 'ids'):
        _deleting_vaults.ids = set()
    _deleting_vaults.ids.add(str(vault_id))


def unmark_vault_deleting(vault_id):
    """Unmark a vault as being deleted."""
    if hasattr(_deleting_vaults, 'ids'):
        _deleting_vaults.ids.discard(str(vault_id))


@receiver(pre_delete, sender=Vault)
def mark_vault_as_deleting(sender, instance, **kwargs):
    """Mark vault as being deleted to prevent cascade audit log attempts."""
    mark_vault_deleting(instance.id)


@receiver(post_delete, sender=Vault)
def unmark_vault_as_deleting(sender, instance, **kwargs):
    """Unmark vault after deletion is complete."""
    unmark_vault_deleting(instance.id)


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


@receiver(post_save, sender=VaultMembership)
def broadcast_membership_added(sender, instance, created, **kwargs):
    """
    Broadcast member.added event via WebSocket when a new member is added to a vault.
    """
    if created:
        # Import inside handler to avoid circular imports
        from apps.vaults.tasks import broadcast_member_added
        broadcast_member_added.delay(  # type: ignore[attr-defined]
            membership_id=str(instance.id)
        )


@receiver(pre_save, sender=VaultMembership)
def log_membership_role_changed(sender, instance, **kwargs):
    """
    Log when a member's role is changed.
    """
    # Only check if this is an update (pk exists)
    if instance.pk:
        try:
            old_membership = VaultMembership.objects.get(pk=instance.pk)
            # Check if role has changed
            if old_membership.role != instance.role:
                metadata = {
                    'user_id': str(instance.user.id),
                    'old_role': old_membership.role,
                    'new_role': instance.role
                }
                AuditLog.objects.create(
                    vault=instance.vault,
                    actor=instance.added_by,
                    action='membership.role_changed',
                    metadata=metadata
                )
        except VaultMembership.DoesNotExist:
            # Should not happen, but handle gracefully
            pass


@receiver(post_delete, sender=VaultMembership)
def log_membership_removed(sender, instance, **kwargs):
    """
    Log when a member is removed from a vault.

    Note: This is a fallback for deletions not through the API view.
    The VaultMembershipViewSet.perform_destroy() handles API deletions
    with the actual actor. This signal catches cascade deletes and
    direct ORM deletions where no actor context is available.

    Skips logging during cascade deletes (e.g., when vault is deleted).
    """
    from django.utils import timezone
    from datetime import timedelta

    # Skip if vault is being deleted (cascade delete)
    if is_vault_being_deleted(instance.vault_id):
        return

    try:
        # Check if audit log was already created by the view (within last 2 seconds)
        recent_log = AuditLog.objects.filter(
            vault_id=instance.vault_id,
            action='membership.removed',
            metadata__user_id=str(instance.user.id),
            created_at__gte=timezone.now() - timedelta(seconds=2)
        ).exists()

        if recent_log:
            # Already logged by the view, skip duplicate
            return

        # Fallback: log without actor for cascade/direct deletions
        metadata = {
            'user_id': str(instance.user.id),
            'username': instance.user.username,
            'role': instance.role,
            'note': 'Actor unknown (cascade or direct deletion)',
        }
        AuditLog.objects.create(
            vault_id=instance.vault_id,
            actor=None,
            action='membership.removed',
            metadata=metadata
        )
    except Exception:
        # Don't fail deletion for logging errors
        pass
