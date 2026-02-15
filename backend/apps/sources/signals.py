"""
Signal handlers for Source model changes.

Broadcasts WebSocket events when sources are created, updated, or deleted.
Events are sent asynchronously via Celery to avoid blocking HTTP requests.
Also logs audit events for research integrity tracking.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.sources.models import Source
from apps.vaults.models import AuditLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Source)
def source_saved(sender, instance, created, **kwargs):
    """
    Handle Source post_save signal.

    Enqueues Celery tasks to broadcast source.created or source.updated
    events to all vault collaborators.

    On source creation, also triggers metadata enrichment via DOI/ISBN lookup.
    """
    from apps.sources.tasks import broadcast_source_created, broadcast_source_updated, enrich_source_metadata

    if created:
        # New source created - broadcast creation event
        logger.info(f"Source {instance.id} created in vault {instance.vault_id}, enqueueing broadcast task")
        broadcast_source_created.delay(instance.id)  # type: ignore[attr-defined]

        # Trigger metadata enrichment (US-022)
        logger.info(f"Enqueueing metadata enrichment task for source {instance.id}")
        enrich_source_metadata.delay(instance.id)  # type: ignore[attr-defined]
    else:
        # Existing source updated - broadcast update event
        # Track changed fields for minimal updates
        changed_fields = []
        if hasattr(instance, '_changed_fields'):
            changed_fields = list(instance._changed_fields)

        logger.info(f"Source {instance.id} updated in vault {instance.vault_id}, enqueueing broadcast task")
        broadcast_source_updated.delay(instance.id, changed_fields)  # type: ignore[attr-defined]


@receiver(post_save, sender=Source)
def log_source_mutation(sender, instance, created, **kwargs):
    """
    Log source creation and updates to audit trail for research integrity.
    """
    try:
        if created:
            # Log source.created
            AuditLog.objects.create(
                vault=instance.vault,
                actor=instance.created_by,
                action='source.created',
                metadata={
                    'source_id': instance.id,
                    'title': instance.title,
                    'url': instance.url,
                    'source_type': instance.source_type,
                }
            )
            logger.info(f"Audit log: source.created for source {instance.id}")
        else:
            # Log source.updated with changed fields
            dirty_fields = instance.get_dirty_fields() if hasattr(instance, 'get_dirty_fields') else {}

            # Only log if there are actual changes (exclude auto-updated fields)
            changes = {k: str(v) for k, v in dirty_fields.items() if k not in ['updated_at', 'search_vector']}

            if changes:
                AuditLog.objects.create(
                    vault=instance.vault,
                    actor=instance.created_by,  # Best available - actual updater not tracked
                    action='source.updated',
                    metadata={
                        'source_id': instance.id,
                        'title': instance.title,
                        'changed_fields': list(changes.keys()),
                    }
                )
                logger.info(f"Audit log: source.updated for source {instance.id}, fields: {list(changes.keys())}")
    except Exception as e:
        # Log but don't fail the save operation
        logger.warning(f"Failed to create audit log for source {instance.id}: {e}", exc_info=True)


@receiver(post_delete, sender=Source)
def source_deleted(sender, instance, **kwargs):
    """
    Handle Source post_delete signal.

    Enqueues Celery task to broadcast source.deleted event to all vault collaborators.
    """
    from apps.sources.tasks import broadcast_source_deleted

    logger.info(f"Source {instance.id} deleted from vault {instance.vault_id}, enqueueing broadcast task")

    # Broadcast deletion event with minimal info (source already deleted from DB)
    broadcast_source_deleted.delay(  # type: ignore[attr-defined]
        source_id=instance.id,
        vault_id=instance.vault_id,
        deleted_by_id=instance.created_by_id if instance.created_by else None
    )


@receiver(post_delete, sender=Source)
def log_source_deleted(sender, instance, **kwargs):
    """
    Log source deletion to audit trail for research integrity.

    Note: Actor is set to created_by as the actual deleter is not available
    in the post_delete signal. For accurate tracking, use the view-level
    audit logging instead.

    Skips logging during cascade deletes (e.g., when vault is deleted).
    """
    from apps.vaults.signals import is_vault_being_deleted

    # Skip if vault is being deleted (cascade delete)
    if is_vault_being_deleted(instance.vault_id):
        logger.debug(f"Skipping audit log for source {instance.id} - vault was deleted (cascade)")
        return

    try:
        AuditLog.objects.create(
            vault_id=instance.vault_id,
            actor=instance.created_by,  # Best available - actual deleter not tracked in signal
            action='source.deleted',
            metadata={
                'source_id': instance.id,
                'title': instance.title,
                'url': instance.url,
                'source_type': instance.source_type,
            }
        )
        logger.info(f"Audit log: source.deleted for source {instance.id}")
    except Exception as e:
        # Log but don't fail the delete operation
        logger.warning(f"Failed to create audit log for deleted source {instance.id}: {e}", exc_info=True)
