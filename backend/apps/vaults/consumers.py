"""
WebSocket consumers for real-time vault collaboration.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from apps.vaults.models import VaultMembership  # type: ignore[import-not-found]

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
        4. On success: accept connection
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
        logger.info(f"User {user.id} connected to vault {self.vault_id}")

    async def disconnect(self, code: int) -> None:
        """
        Handle WebSocket disconnection and cleanup.

        Args:
            code: WebSocket close code
        """
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
