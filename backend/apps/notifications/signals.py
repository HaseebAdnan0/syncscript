"""
Signal handlers for notification creation.

Listens to model changes and creates notifications for relevant events.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.vaults.models import VaultMembership
from apps.sources.models import Source
from apps.annotations.models import Annotation
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


@receiver(post_save, sender=Source)
def source_created(sender, instance, created, **kwargs):  # type: ignore[misc]
    """
    Handle Source post_save signal.

    Creates source_added notifications for all vault members except the creator
    when a new source is added to the vault.
    """
    del sender, kwargs  # Mark unused but required params

    if not created:
        # Only handle new sources, not updates
        return

    # Get creator name (or "Unknown" if created_by is None)
    creator_name = instance.created_by.username if instance.created_by else "Unknown"

    # Get all vault members
    vault_members = instance.vault.members.all()

    # Notify each member except the creator
    for member in vault_members:
        # Skip the creator
        if instance.created_by and member.id == instance.created_by.id:
            continue

        notification = create_notification(
            user=member,
            notification_type="source_added",
            title=f"New source in {instance.vault.name}",
            body=f"{creator_name} added \"{instance.title}\" to {instance.vault.name}",
            data={
                "vault_id": str(instance.vault.id),
                "vault_name": instance.vault.name,
                "source_id": instance.id,
                "source_title": instance.title,
                "creator_name": creator_name,
            },
        )

        if notification:
            logger.info(
                f"Created source_added notification for user {member.id} "
                f"about source {instance.id} in vault {instance.vault.id}"
            )
        else:
            logger.debug(
                f"Skipped source_added notification for user {member.id} "
                f"(preferences or mute)"
            )


@receiver(post_save, sender=Annotation)
def annotation_created(sender, instance, created, **kwargs):  # type: ignore[misc]
    """
    Handle Annotation post_save signal.

    Creates annotation_reply notification for the parent annotation author
    when someone replies to their annotation.
    """
    del sender, kwargs  # Mark unused but required params

    if not created:
        # Only handle new annotations, not updates
        return

    # Only handle replies (annotations with a parent)
    if not instance.parent:
        return

    # Don't notify if replying to own annotation
    if instance.parent.user == instance.user:
        return

    # Get preview of reply content (first 100 chars)
    preview = instance.content[:100] + "..." if len(instance.content) > 100 else instance.content

    notification = create_notification(
        user=instance.parent.user,
        notification_type="annotation_reply",
        title=f"Reply to your annotation",
        body=f"{instance.user.username} replied to your annotation: {preview}",
        data={
            "source_id": instance.source.id,
            "annotation_id": instance.id,
            "parent_id": instance.parent.id,
            "replier_name": instance.user.username,
            "preview": preview,
        },
    )

    if notification:
        logger.info(
            f"Created annotation_reply notification for user {instance.parent.user.id} "
            f"about reply {instance.id} to annotation {instance.parent.id}"
        )
    else:
        logger.debug(
            f"Skipped annotation_reply notification for user {instance.parent.user.id} "
            f"(preferences or mute)"
        )
