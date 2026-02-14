"""
Celery tasks for broadcasting VaultMembership events via WebSocket.
"""
import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def broadcast_member_added(membership_id: str) -> None:
    """
    Broadcast member.added event when a new member is added to a vault.

    Args:
        membership_id: UUID of the VaultMembership instance
    """
    # Import models inside task to avoid circular imports
    from apps.vaults.models import VaultMembership  # type: ignore[import-not-found]
    from core.websocket_utils import broadcast_to_vault  # type: ignore[import-not-found]

    try:
        # Fetch membership with related user and vault
        membership = VaultMembership.objects.select_related(
            'user', 'vault', 'added_by'
        ).get(id=membership_id)

        # Build payload with member details
        payload: dict[str, Any] = {
            'member': {
                'user_id': membership.user.id,  # type: ignore[attr-defined]
                'username': membership.user.username,  # type: ignore[attr-defined]
                'role': membership.role,  # type: ignore[attr-defined]
                'added_at': membership.added_at.isoformat(),  # type: ignore[attr-defined]
            }
        }

        # Add added_by info if available
        if membership.added_by:  # type: ignore[attr-defined]
            payload['member']['added_by'] = {
                'user_id': membership.added_by.id,  # type: ignore[attr-defined]
                'username': membership.added_by.username,  # type: ignore[attr-defined]
            }

        # Broadcast to vault room
        broadcast_to_vault(
            vault_id=str(membership.vault.id),  # type: ignore[attr-defined]
            event_type='member.added',
            payload=payload,
            user=membership.added_by if membership.added_by else None  # type: ignore[attr-defined]
        )

        logger.info(f"Broadcast member.added for membership {membership_id}")

    except VaultMembership.DoesNotExist:  # type: ignore[misc]
        logger.error(f"VaultMembership {membership_id} not found for broadcast")
