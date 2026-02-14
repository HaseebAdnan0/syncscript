"""
Signal handlers for notification creation.

Listens to model changes and creates notifications for relevant events.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.vaults.models import VaultMembership
from apps.notifications.services import create_notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=VaultMembership)
def vault_membership_created(sender, instance, created, **kwargs):  # type: ignore[misc]
    """
    Handle VaultMembership post_save signal.

    Creates a vault_invite notification when a user is added to a vault
    (as long as they're not the vault owner).

    Also creates a member_joined notification for the vault owner when
    someone joins their vault.
    """
    del sender, kwargs  # Mark unused but required params

    if not created:
        # Only handle new memberships, not updates
        return

    # Don't notify if the new member is the vault owner (auto-created membership)
    if instance.user == instance.vault.owner:
        return

    # Get inviter name (or "Unknown" if added_by is None)
    inviter_name = instance.added_by.username if instance.added_by else "Unknown"

    # Create vault_invite notification for the new member
    invite_notification = create_notification(
        user=instance.user,
        notification_type="vault_invite",
        title=f"Invited to {instance.vault.name}",
        body=f"{inviter_name} invited you to join {instance.vault.name}",
        data={
            "vault_id": str(instance.vault.id),
            "vault_name": instance.vault.name,
            "inviter_id": instance.added_by.id if instance.added_by else None,
            "inviter_name": inviter_name,
        },
    )

    if invite_notification:
        logger.info(
            f"Created vault_invite notification for user {instance.user.id} "
            f"to vault {instance.vault.id}"
        )
    else:
        logger.debug(
            f"Skipped vault_invite notification for user {instance.user.id} "
            f"(preferences or mute)"
        )

    # Create member_joined notification for the vault owner
    # (only if owner is different from the new member)
    if instance.vault.owner != instance.user:
        member_notification = create_notification(
            user=instance.vault.owner,
            notification_type="member_joined",
            title=f"New member in {instance.vault.name}",
            body=f"{instance.user.username} joined {instance.vault.name}",
            data={
                "vault_id": str(instance.vault.id),
                "vault_name": instance.vault.name,
                "member_id": instance.user.id,
                "member_name": instance.user.username,
            },
        )

        if member_notification:
            logger.info(
                f"Created member_joined notification for owner {instance.vault.owner.id} "
                f"about user {instance.user.id}"
            )
        else:
            logger.debug(
                f"Skipped member_joined notification for owner {instance.vault.owner.id} "
                f"(preferences or mute)"
            )
