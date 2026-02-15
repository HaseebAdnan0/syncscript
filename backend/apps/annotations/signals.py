"""
Signal handlers for Annotation model to broadcast real-time events via WebSocket.
Also logs audit events for research integrity tracking.
"""
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from apps.annotations.models import Annotation
from apps.vaults.models import AuditLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Annotation)
def annotation_post_save(sender, instance, created, **kwargs):  # type: ignore[no-untyped-def]  # noqa: ARG001
    """
    Broadcast annotation.created event when a new annotation is created.
    Only broadcasts for created=True (not for updates).
    """
    if created:
        # Import inside handler to avoid circular imports
        from apps.annotations.tasks import broadcast_annotation_created  # type: ignore[import-not-found]

        # Enqueue Celery task for async broadcasting
        broadcast_annotation_created.delay(instance.id)  # type: ignore[attr-defined]
        logger.info(f"Enqueued broadcast_annotation_created for annotation {instance.id}")


@receiver(post_save, sender=Annotation)
def log_annotation_change(sender, instance, created, **kwargs):  # type: ignore[no-untyped-def]  # noqa: ARG001
    """
    Log annotation creation and updates to audit trail for research integrity.
    """
    try:
        if created:
            # Determine if this is a reply or top-level annotation
            if instance.parent:
                # Log annotation.replied
                AuditLog.objects.create(
                    vault=instance.source.vault,
                    actor=instance.user,
                    action='annotation.replied',
                    metadata={
                        'annotation_id': instance.id,
                        'source_id': instance.source_id,
                        'parent_id': instance.parent_id,
                        'content_preview': instance.content[:100] if instance.content else '',
                    }
                )
                logger.info(f"Audit log: annotation.replied for annotation {instance.id}")
            else:
                # Log annotation.created
                AuditLog.objects.create(
                    vault=instance.source.vault,
                    actor=instance.user,
                    action='annotation.created',
                    metadata={
                        'annotation_id': instance.id,
                        'source_id': instance.source_id,
                        'page_number': instance.page_number,
                        'content_preview': instance.content[:100] if instance.content else '',
                    }
                )
                logger.info(f"Audit log: annotation.created for annotation {instance.id}")
        else:
            # Log annotation.updated with content diff
            dirty_fields = instance.get_dirty_fields() if hasattr(instance, 'get_dirty_fields') else {}

            # Only log if there are actual changes (exclude auto-updated fields)
            changes = {k: str(v) for k, v in dirty_fields.items() if k not in ['updated_at']}

            if changes:
                AuditLog.objects.create(
                    vault=instance.source.vault,
                    actor=instance.user,
                    action='annotation.updated',
                    metadata={
                        'annotation_id': instance.id,
                        'source_id': instance.source_id,
                        'changed_fields': list(changes.keys()),
                        'content_preview': instance.content[:100] if instance.content else '',
                    }
                )
                logger.info(f"Audit log: annotation.updated for annotation {instance.id}, fields: {list(changes.keys())}")
    except Exception as e:
        # Log but don't fail the save operation
        logger.warning(f"Failed to create audit log for annotation {instance.id}: {e}", exc_info=True)


@receiver(pre_delete, sender=Annotation)
def log_annotation_delete(sender, instance, **kwargs):  # type: ignore[no-untyped-def]  # noqa: ARG001
    """
    Log annotation deletion to audit trail for research integrity.

    Uses pre_delete signal to capture annotation data before it's removed from database.
    """
    try:
        AuditLog.objects.create(
            vault=instance.source.vault,
            actor=instance.user,
            action='annotation.deleted',
            metadata={
                'annotation_id': instance.id,
                'source_id': instance.source_id,
                'parent_id': instance.parent_id if instance.parent else None,
                'content_preview': instance.content[:100] if instance.content else '',
            }
        )
        logger.info(f"Audit log: annotation.deleted for annotation {instance.id}")
    except Exception as e:
        # Log but don't fail the delete operation
        logger.warning(f"Failed to create audit log for deleted annotation {instance.id}: {e}", exc_info=True)
