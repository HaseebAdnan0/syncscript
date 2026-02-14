"""
Signal handlers for Annotation model to broadcast real-time events via WebSocket.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.annotations.models import Annotation

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
