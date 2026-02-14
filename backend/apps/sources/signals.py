"""
Signal handlers for Source model changes.

Broadcasts WebSocket events when sources are created, updated, or deleted.
Events are sent asynchronously via Celery to avoid blocking HTTP requests.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.sources.models import Source

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Source)
def source_saved(sender, instance, created, **kwargs):
    """
    Handle Source post_save signal.

    Enqueues Celery tasks to broadcast source.created or source.updated
    events to all vault collaborators.
    """
    from apps.sources.tasks import broadcast_source_created, broadcast_source_updated

    if created:
        # New source created - broadcast creation event
        logger.info(f"Source {instance.id} created in vault {instance.vault_id}, enqueueing broadcast task")
        broadcast_source_created.delay(instance.id)
    else:
        # Existing source updated - broadcast update event
        # Track changed fields for minimal updates
        changed_fields = []
        if hasattr(instance, '_changed_fields'):
            changed_fields = list(instance._changed_fields)

        logger.info(f"Source {instance.id} updated in vault {instance.vault_id}, enqueueing broadcast task")
        broadcast_source_updated.delay(instance.id, changed_fields)


@receiver(post_delete, sender=Source)
def source_deleted(sender, instance, **kwargs):
    """
    Handle Source post_delete signal.

    Enqueues Celery task to broadcast source.deleted event to all vault collaborators.
    """
    from apps.sources.tasks import broadcast_source_deleted

    logger.info(f"Source {instance.id} deleted from vault {instance.vault_id}, enqueueing broadcast task")

    # Broadcast deletion event with minimal info (source already deleted from DB)
    broadcast_source_deleted.delay(
        source_id=instance.id,
        vault_id=instance.vault_id,
        deleted_by_id=instance.created_by_id if instance.created_by else None
    )
