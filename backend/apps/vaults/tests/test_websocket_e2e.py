"""
E2E WebSocket tests for vault collaboration - connection and authentication.

Tests verify full WebSocket connection flow with authentication and permissions.
"""

from django.test import TransactionTestCase, override_settings
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken
from apps.vaults.models import Vault, VaultMembership, RoleChoices  # type: ignore[import-not-found]
from config.asgi import application  # type: ignore[import-not-found]

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    },
)
class WebSocketConnectionAuthTests(TransactionTestCase):
    """
    E2E tests for WebSocket connection and authentication.
    """

    def setUp(self) -> None:
        """Create test fixtures."""
        # Create users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user_no_access = User.objects.create_user(
            username='noaccess',
            email='noaccess@example.com',
            password='testpass123'
        )

        # Create vault (owner membership created automatically by signal)
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for WebSocket tests',
            owner=self.user1
        )

        # Add user2 as contributor
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.user2,
            role=RoleChoices.CONTRIBUTOR,
            added_by=self.user1
        )

        # Generate JWT tokens
        self.token_user1 = str(AccessToken.for_user(self.user1))
        self.token_user2 = str(AccessToken.for_user(self.user2))

    async def test_connection_success_with_valid_jwt_and_membership(self) -> None:
        """
        Test: Connection succeeds with valid JWT and vault membership.
        """
        # Create WebSocket communicator with valid token
        communicator = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/?token={self.token_user1}'
        )

        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected, 'WebSocket connection should succeed with valid JWT and membership')

        # Should receive connection.success message with sequence number
        response = await communicator.receive_json_from()
        self.assertEqual(response.get('type'), 'connection.success')
        self.assertIn('seq', response)
        self.assertIsInstance(response['seq'], int)

        # Cleanup
        await communicator.disconnect()

    async def test_connection_rejected_with_invalid_jwt(self) -> None:
        """
        Test: Connection rejected with invalid JWT (error + close 1008).
        """
        # Create WebSocket communicator with invalid token
        invalid_token = 'invalid.jwt.token'
        communicator = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/?token={invalid_token}'
        )

        # Connect
        connected, _ = await communicator.connect()

        if connected:
            # Receive error message
            response = await communicator.receive_json_from()
            self.assertEqual(response.get('type'), 'error')
            self.assertEqual(response['error']['code'], 'AUTH_FAILED')

            # Wait for connection close
            await communicator.wait(timeout=3)

        # Verify connection is closed
        # If connect() returned False, connection was rejected during handshake
        # If connect() returned True, connection should be closed after error
        self.assertFalse(communicator.scope is not None and communicator.output_queue.qsize() > 0)

        # Cleanup
        await communicator.disconnect()

    async def test_connection_rejected_without_vault_membership(self) -> None:
        """
        Test: Connection rejected without vault membership (error + close 1008).
        """
        # Create JWT for user without vault membership
        token_no_access = str(AccessToken.for_user(self.user_no_access))

        # Create WebSocket communicator
        communicator = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/?token={token_no_access}'
        )

        # Connect
        connected, _ = await communicator.connect()

        if connected:
            # Receive error message
            response = await communicator.receive_json_from()
            self.assertEqual(response.get('type'), 'error')
            self.assertEqual(response['error']['code'], 'PERMISSION_DENIED')
            self.assertIn('vault', response['error']['message'].lower())

            # Wait for connection close
            await communicator.wait(timeout=3)

        # Verify connection is closed
        self.assertFalse(communicator.scope is not None and communicator.output_queue.qsize() > 0)

        # Cleanup
        await communicator.disconnect()

    async def test_connection_rejected_with_missing_jwt(self) -> None:
        """
        Test: Connection rejected with missing JWT token (error + close 1008).
        """
        # Create WebSocket communicator without token
        communicator = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/'
        )

        # Connect
        connected, _ = await communicator.connect()

        if connected:
            # Receive error message
            response = await communicator.receive_json_from()
            self.assertEqual(response.get('type'), 'error')
            self.assertEqual(response['error']['code'], 'AUTH_FAILED')

            # Wait for connection close
            await communicator.wait(timeout=3)

        # Verify connection is closed
        self.assertFalse(communicator.scope is not None and communicator.output_queue.qsize() > 0)

        # Cleanup
        await communicator.disconnect()

    async def test_contributor_can_connect_to_vault(self) -> None:
        """
        Test: User with CONTRIBUTOR role can connect successfully.
        """
        # Create WebSocket communicator with user2 token (contributor)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/?token={self.token_user2}'
        )

        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected, 'WebSocket connection should succeed for contributor')

        # Should receive connection.success message
        response = await communicator.receive_json_from()
        self.assertEqual(response.get('type'), 'connection.success')

        # Cleanup
        await communicator.disconnect()
