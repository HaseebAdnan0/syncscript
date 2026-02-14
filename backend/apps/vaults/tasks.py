"""
Celery tasks for broadcasting VaultMembership events via WebSocket.
"""
import logging
import time
from typing import Any

from celery import shared_task
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer  # type: ignore[import-untyped]

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


@shared_task
def cleanup_stale_connections() -> None:
    """
    Periodic task to disconnect idle WebSocket connections.

    Runs every 60 seconds. Checks all vault presence sets for users who
    haven't sent a heartbeat in > 300 seconds (5 minutes) and closes
    their connections.

    This is Layer 4 rate limiting - idle connection cleanup.
    """
    redis_conn = cache.client.get_client()  # type: ignore[attr-defined]
    channel_layer = get_channel_layer()

    # Get all keys matching vault presence pattern
    presence_keys = redis_conn.keys('vault_*:presence')

    current_time = time.time()
    timeout_threshold = 300  # 5 minutes
    stale_cutoff = current_time - timeout_threshold

    total_disconnected = 0

    for presence_key in presence_keys:
        # Get all users in this vault's presence with timestamps
        # zrangebyscore returns members with score <= stale_cutoff
        stale_entries = redis_conn.zrangebyscore(
            presence_key,
            '-inf',  # From negative infinity
            stale_cutoff,  # Up to stale cutoff timestamp
            withscores=True
        )

        if not stale_entries:
            continue

        # Extract vault_id from presence key (format: vault_{id}:presence)
        vault_id = presence_key.decode('utf-8').split('_')[1].split(':')[0]

        for entry in stale_entries:
            # Entry is tuple: (member, score)
            # Member is user_id (bytes), score is timestamp
            user_id_bytes, last_heartbeat = entry
            user_id = user_id_bytes.decode('utf-8')

            # Get user's connection channels from user_{id}:connections
            connections_key = f"user_{user_id}:connections"
            user_channels = redis_conn.zrange(connections_key, 0, -1)

            # Send close message to all user's connections in this vault
            for channel_name_bytes in user_channels:
                channel_name = channel_name_bytes.decode('utf-8')

                # Send close_connection message via channel layer
                async_to_sync(channel_layer.send)(  # type: ignore[arg-type]
                    channel_name,
                    {
                        'type': 'close_connection',
                        'code': 1000,  # Normal closure - idle timeout
                        'reason': 'Connection idle for > 5 minutes'
                    }
                )

                total_disconnected += 1
                logger.info(
                    f"Disconnecting stale connection: user_id={user_id}, "
                    f"vault_id={vault_id}, channel={channel_name}, "
                    f"last_heartbeat={int(current_time - last_heartbeat)}s ago"
                )

            # Remove user from presence set
            redis_conn.zrem(presence_key, user_id)

    if total_disconnected > 0:
        logger.info(f"Cleanup task disconnected {total_disconnected} stale connections")

    # Clean up empty presence sets to prevent Redis bloat
    for presence_key in presence_keys:
        if redis_conn.zcard(presence_key) == 0:
            redis_conn.delete(presence_key)
