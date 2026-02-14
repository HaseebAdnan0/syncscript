"""
WebSocket utility functions for broadcasting events to vault rooms.
"""
import json
from typing import Any, Optional
from datetime import datetime, timezone

from django.core.cache import cache
from channels.layers import get_channel_layer  # type: ignore[import-untyped]
from asgiref.sync import async_to_sync


def broadcast_to_vault(
    vault_id: int,
    event_type: str,
    payload: dict[str, Any],
    user: Optional[Any] = None,
) -> None:
    """
    Broadcast an event to all users in a vault room.

    Args:
        vault_id: ID of the vault to broadcast to
        event_type: Type of event (e.g., 'source.created', 'annotation.created')
        payload: Event payload data
        user: User who triggered the event (optional)

    This function:
    1. Increments the sequence number in Redis
    2. Builds a message envelope with type, seq, event, payload, metadata
    3. Sends the message via channel_layer.group_send
    """
    # Get Redis client to manage sequence numbers
    redis_client = cache.client.get_client()  # type: ignore[attr-defined]

    # Increment sequence number for this vault
    seq_key = f"vault_{vault_id}:seq"
    seq_number = redis_client.incr(seq_key)

    # Build message envelope
    message = {
        "type": event_type,
        "seq": seq_number,
        "event": event_type,
        "payload": payload,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vault_id": vault_id,
        }
    }

    # Add user info to metadata if provided
    if user:
        message["metadata"]["user_id"] = user.id  # type: ignore[attr-defined]
        message["metadata"]["username"] = user.username  # type: ignore[attr-defined]

    # Send to channel layer
    channel_layer = get_channel_layer()
    group_name = f"vault_{vault_id}"

    # Convert message to format expected by group_send
    # The 'type' field maps to the consumer method name (vault_event)
    group_message = {
        "type": "vault_event",
        "message": json.dumps(message),
    }

    async_to_sync(channel_layer.group_send)(group_name, group_message)  # type: ignore[union-attr]

    # Buffer event in Redis for replay
    events_key = f"vault_{vault_id}:events"
    event_json = json.dumps(message)

    # Add event to list (newest at head)
    redis_client.lpush(events_key, event_json)

    # Keep only last 100 events
    redis_client.ltrim(events_key, 0, 99)

    # Set 1-hour TTL on events list
    redis_client.expire(events_key, 3600)
