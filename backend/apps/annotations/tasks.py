"""
Celery tasks for broadcasting Annotation events to WebSocket clients.
"""
import logging
from typing import Any
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def broadcast_annotation_created(annotation_id: int) -> None:
    """
    Broadcast annotation.created event to all vault members.

    Args:
        annotation_id: ID of the created annotation
    """
    from apps.annotations.models import Annotation  # type: ignore[import-not-found]
    from core.websocket_utils import broadcast_to_vault  # type: ignore[import-not-found]

    try:
        annotation = Annotation.objects.select_related('source', 'user', 'source__vault').get(id=annotation_id)

        # Build payload matching event catalog
        payload: dict[str, Any] = {
            'id': annotation.id,  # type: ignore[attr-defined]
            'source_id': annotation.source.id,  # type: ignore[attr-defined]
            'content': annotation.content,  # type: ignore[attr-defined]
            'page_number': annotation.page_number,  # type: ignore[attr-defined]
            'position': annotation.position,  # type: ignore[attr-defined]
            'parent_id': annotation.parent_id,  # type: ignore[attr-defined]
            'created_by': {
                'id': annotation.user.id,  # type: ignore[attr-defined]
                'username': annotation.user.username,  # type: ignore[attr-defined]
            },
            'created_at': annotation.created_at.isoformat(),  # type: ignore[attr-defined]
        }

        # Broadcast to vault
        broadcast_to_vault(
            vault_id=annotation.source.vault.id,  # type: ignore[attr-defined]
            event_type='annotation.created',
            payload=payload,
            user=annotation.user
        )

        logger.info(f"Broadcast annotation.created for annotation {annotation_id} to vault {annotation.source.vault.id}")  # type: ignore[attr-defined]

    except Annotation.DoesNotExist:
        logger.error(f"Annotation {annotation_id} not found, cannot broadcast")
