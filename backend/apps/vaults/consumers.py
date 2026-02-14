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

        if hasattr(self, 'user') and hasattr(self, 'vault_id'):
            logger.info(f"User {self.user.id} disconnected from vault {self.vault_id} (code: {code})")

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
                    'username': user.username,
                    'joined_at': int(timestamp),
                    'status': status
                })
            except User.DoesNotExist:
                # User was deleted, remove from presence
                redis_conn.zrem(presence_key, str(user_id))

        return presence_list
