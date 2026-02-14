"""
WebSocket consumers for real-time vault collaboration.
"""

import json
import logging
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.vaults.models import VaultMembership  # type: ignore[import-not-found]

User = get_user_model()
logger = logging.getLogger('channels.vault.consumer')


class VaultConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for vault rooms.

    Handles real-time collaboration within knowledge vaults.
    """

    async def connect(self) -> None:
        """
        Accept or reject WebSocket connection based on authentication and permissions.

        Steps:
        1. Extract vault_id from URL kwargs
        2. Check user is authenticated (not AnonymousUser)
        3. Verify user has vault membership (any role)
        4. On success: accept connection and join room
        5. On failure: send error JSON and close with code 1008
        """
        # Extract vault_id from URL kwargs
        url_route = self.scope.get('url_route', {})  # type: ignore[typeddict-item]
        vault_id_str = url_route.get('kwargs', {}).get('vault_id')
        if not vault_id_str:
            await self._send_error_and_close('VAULT_NOT_FOUND', 'Vault ID not provided')
            return

        try:
            self.vault_id = int(vault_id_str)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            await self._send_error_and_close('VAULT_NOT_FOUND', 'Invalid vault ID format')
            return

        # Check user is authenticated
        user = self.scope.get('user')
        if not user or isinstance(user, AnonymousUser):
            await self._send_error_and_close('AUTH_FAILED', 'Authentication required')
            return

        self.user = user  # Store for later use

        # Verify user has vault membership
        has_membership = await self._check_vault_membership(user.id, self.vault_id)
        if not has_membership:
            await self._send_error_and_close('PERMISSION_DENIED', 'No access to this vault')
            return

        # Accept connection
        await self.accept()

        # Join vault room group
        self.room_group_name = f"vault_{self.vault_id}"
        await self.channel_layer.group_add(  # type: ignore[union-attr]
            self.room_group_name,
            self.channel_name
        )

        # Get current sequence number (placeholder - will be implemented with Redis in later tasks)
        sequence_number = 0

        # Add user to presence tracking
        await self._add_to_presence(user.id, self.vault_id)

        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection.success',
            'seq': sequence_number,
            'vault_id': self.vault_id
        }))

        # Broadcast presence update to all room members
        await self._broadcast_presence_update()

        logger.info(f"User {user.id} connected to vault {self.vault_id}")

    async def disconnect(self, code: int) -> None:
        """
        Handle WebSocket disconnection and cleanup.

        Args:
            code: WebSocket close code
        """
        # Remove user from presence tracking
        if hasattr(self, 'user') and hasattr(self, 'vault_id'):
            await self._remove_from_presence(self.user.id, self.vault_id)

        # Leave vault room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(  # type: ignore[union-attr]
                self.room_group_name,
                self.channel_name
            )

            # Broadcast updated presence to remaining members
            if hasattr(self, 'vault_id'):
                await self._broadcast_presence_update()

        if hasattr(self, 'user') and hasattr(self, 'vault_id'):
            logger.info(f"User {self.user.id} disconnected from vault {self.vault_id} (code: {code})")

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        """
        Handle incoming WebSocket messages from clients.

        Args:
            text_data: JSON string containing the message
            bytes_data: Binary data (not used in this implementation)
        """
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'heartbeat':
                # Update user's timestamp in presence tracking
                await self._update_presence(self.user.id, self.vault_id)
            elif message_type == 'replay_request':
                # Replay missed events since given sequence number
                since_seq = data.get('since_seq', 0)
                await self._replay_events(since_seq)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    @database_sync_to_async
    def _check_vault_membership(self, user_id: int, vault_id: int) -> bool:
        """
        Check if user has any membership in the vault.

        Args:
            user_id: User ID to check
            vault_id: Vault ID to check

        Returns:
            True if user is a member, False otherwise
        """
        return VaultMembership.objects.filter(
            user_id=user_id,
            vault_id=vault_id
        ).exists()

    async def _send_error_and_close(self, code: str, message: str) -> None:
        """
        Send error message and close connection with code 1008 (policy violation).

        Args:
            code: Error code (e.g., 'AUTH_FAILED', 'PERMISSION_DENIED')
            message: Human-readable error message
        """
        error_payload = {
            'type': 'error',
            'error': {
                'code': code,
                'message': message
            }
        }

        try:
            await self.send(text_data=json.dumps(error_payload))
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

        await self.close(code=1008)  # Policy violation
        logger.warning(f"Connection rejected: {code} - {message}")

    async def vault_event(self, event: dict) -> None:
        """
        Receive messages from vault room group and forward to WebSocket client.

        Args:
            event: Event dictionary from channel layer containing message data
        """
        # Forward the event to the WebSocket client
        await self.send(text_data=json.dumps(event))

    async def _add_to_presence(self, user_id: int, vault_id: int) -> None:
        """
        Add user to Redis sorted set for presence tracking.

        Args:
            user_id: User ID to add
            vault_id: Vault ID for the presence set
        """
        presence_key = f"vault_{vault_id}:presence"
        timestamp = time.time()

        # Add to sorted set with current timestamp as score
        redis_conn = cache.client.get_client()  # type: ignore[attr-defined]
        redis_conn.zadd(presence_key, {str(user_id): timestamp})

    async def _remove_from_presence(self, user_id: int, vault_id: int) -> None:
        """
        Remove user from Redis sorted set for presence tracking.

        Args:
            user_id: User ID to remove
            vault_id: Vault ID for the presence set
        """
        presence_key = f"vault_{vault_id}:presence"

        # Remove from sorted set
        redis_conn = cache.client.get_client()  # type: ignore[attr-defined]
        redis_conn.zrem(presence_key, str(user_id))

    async def _update_presence(self, user_id: int, vault_id: int) -> None:
        """
        Update user's timestamp in Redis sorted set for presence tracking.

        This is called on heartbeat to keep the connection alive.

        Args:
            user_id: User ID to update
            vault_id: Vault ID for the presence set
        """
        presence_key = f"vault_{vault_id}:presence"
        timestamp = time.time()

        # Update timestamp in sorted set
        redis_conn = cache.client.get_client()  # type: ignore[attr-defined]
        redis_conn.zadd(presence_key, {str(user_id): timestamp})

    @database_sync_to_async
    def _get_presence_list(self, vault_id: int) -> list[dict]:
        """
        Fetch presence list with user details from Redis.

        Args:
            vault_id: Vault ID for the presence set

        Returns:
            List of dicts with user_id, username, joined_at, status
        """
        presence_key = f"vault_{vault_id}:presence"
        redis_conn = cache.client.get_client()  # type: ignore[attr-defined]

        # Get all users with their timestamps
        user_scores = redis_conn.zrange(presence_key, 0, -1, withscores=True)

        current_time = time.time()
        presence_list = []

        for user_id_bytes, timestamp in user_scores:
            user_id = int(user_id_bytes)
            time_since = current_time - timestamp

            # Determine status based on time since last update
            if time_since < 60:
                status = 'active'
            elif time_since < 300:
                status = 'idle'
            else:
                # User is stale, skip
                continue

            # Fetch user details from database
            try:
                user = User.objects.get(id=user_id)
                presence_list.append({
                    'user_id': user_id,
                    'username': user.username,  # type: ignore[attr-defined]
                    'joined_at': int(timestamp),
                    'status': status
                })
            except User.DoesNotExist:
                # User was deleted, remove from presence
                redis_conn.zrem(presence_key, str(user_id))

        return presence_list

    async def _broadcast_presence_update(self) -> None:
        """
        Broadcast presence update to all vault room members.

        Sends a presence.update event with the current list of active users.
        """
        # Get current presence list
        presence_list = await self._get_presence_list(self.vault_id)

        # Broadcast to all room members
        await self.channel_layer.group_send(  # type: ignore[union-attr]
            self.room_group_name,
            {
                'type': 'vault_event',
                'event_type': 'presence.update',
                'payload': {
                    'active_users': presence_list
                },
                'metadata': {
                    'timestamp': int(time.time())
                }
            }
        )

    async def _replay_events(self, since_seq: int) -> None:
        """
        Replay events from Redis buffer to client after reconnection.

        Fetches events from Redis list and sends those with sequence number
        greater than since_seq to the client in chronological order.

        Args:
            since_seq: Sequence number of last event client received
        """
        events_key = f"vault_{self.vault_id}:events"
        redis_conn = cache.client.get_client()  # type: ignore[attr-defined]

        # Fetch all events from Redis list (stored newest-first with lpush)
        events_json = redis_conn.lrange(events_key, 0, -1)

        # Parse events and filter by sequence number
        filtered_events = []
        for event_data in events_json:
            try:
                event = json.loads(event_data)
                event_seq = event.get('seq', 0)

                # Include events with seq > since_seq
                if event_seq > since_seq:
                    filtered_events.append(event)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse event from Redis: {event_data}")

        # Events are stored newest-first, so reverse to get chronological order
        filtered_events.reverse()

        # Send filtered events to client
        for event in filtered_events:
            await self.send(text_data=json.dumps(event))

        logger.info(f"Replayed {len(filtered_events)} events to user {self.user.id} (since_seq={since_seq})")
