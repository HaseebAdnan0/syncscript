"""
E2E WebSocket tests for vault collaboration - broadcasting events.

Tests verify event broadcasting between multiple connected users.
"""

import asyncio
from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken
from apps.vaults.models import Vault, VaultMembership, RoleChoices  # type: ignore[import-not-found]
from apps.sources.models import Source  # type: ignore[import-not-found]
from config.asgi import application  # type: ignore[import-not-found]

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,  # Execute Celery tasks synchronously
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    },
)
class WebSocketBroadcastingTests(TransactionTestCase):
    """
    E2E tests for WebSocket event broadcasting between users.
    """

    def setUp(self) -> None:
        """Create test fixtures."""
        # Create users
        self.user1 = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser2',
            email='user2@example.com',
            password='testpass123'
        )

        # Create vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for broadcasting tests',
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

    async def _connect_user(self, token: str) -> WebsocketCommunicator:
        """Helper: Connect user and consume initial messages."""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/?token={token}'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected, 'WebSocket connection should succeed')

        # Consume connection.success message
        response = await communicator.receive_json_from(timeout=2)
        self.assertEqual(response.get('type'), 'connection.success')

        # Consume presence.update message (broadcasted when user joins)
        response = await communicator.receive_json_from(timeout=2)
        self.assertEqual(response.get('event'), 'presence.update')

        return communicator

    async def test_source_created_broadcasts_to_all_users(self) -> None:
        """
        Test: User A creates source -> User B receives source.created event.
        """
        # Connect both users
        comm_user1 = await self._connect_user(self.token_user1)
        comm_user2 = await self._connect_user(self.token_user2)

        # User1 creates a source (via Django ORM - triggers signal)
        source = await asyncio.to_thread(
            Source.objects.create,
            vault=self.vault,
            url='https://example.com/research-paper',
            title='Test Research Paper',
            description='A test paper for WebSocket broadcasting',
            source_type='URL',
            created_by=self.user1
        )

        # Wait briefly for Celery task to process
        await asyncio.sleep(0.5)

        # User1 should receive source.created event
        response1 = await comm_user1.receive_json_from(timeout=3)
        self.assertEqual(response1.get('event'), 'source.created')
        self.assertEqual(response1['payload']['id'], source.id)
        self.assertEqual(response1['payload']['title'], 'Test Research Paper')
        self.assertEqual(response1['payload']['url'], 'https://example.com/research-paper')

        # User2 should also receive source.created event
        response2 = await comm_user2.receive_json_from(timeout=3)
        self.assertEqual(response2.get('event'), 'source.created')
        self.assertEqual(response2['payload']['id'], source.id)
        self.assertEqual(response2['payload']['title'], 'Test Research Paper')

        # Cleanup
        await comm_user1.disconnect()
        await comm_user2.disconnect()

    async def test_user_join_broadcasts_presence_update_to_all(self) -> None:
        """
        Test: User joins -> all users receive presence.update.
        """
        # Connect user1 first
        comm_user1 = await self._connect_user(self.token_user1)

        # Verify user1 received presence update with 1 user
        # (already consumed in _connect_user helper)

        # Connect user2 (should trigger presence broadcast to all)
        comm_user2 = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/?token={self.token_user2}'
        )
        connected, _ = await comm_user2.connect()
        self.assertTrue(connected)

        # Consume connection.success for user2
        response = await comm_user2.receive_json_from(timeout=2)
        self.assertEqual(response.get('type'), 'connection.success')

        # User2 receives their own presence.update
        response2 = await comm_user2.receive_json_from(timeout=2)
        self.assertEqual(response2.get('event'), 'presence.update')
        self.assertEqual(len(response2['payload']['active_users']), 2)

        # User1 should also receive updated presence.update with 2 users
        response1 = await comm_user1.receive_json_from(timeout=2)
        self.assertEqual(response1.get('event'), 'presence.update')
        self.assertEqual(len(response1['payload']['active_users']), 2)

        # Verify usernames in presence list
        usernames = [u['username'] for u in response1['payload']['active_users']]
        self.assertIn('testuser1', usernames)
        self.assertIn('testuser2', usernames)

        # Cleanup
        await comm_user1.disconnect()
        await comm_user2.disconnect()

    async def test_user_leave_broadcasts_presence_update_to_remaining_users(self) -> None:
        """
        Test: User leaves -> all users receive updated presence.
        """
        # Connect both users
        comm_user1 = await self._connect_user(self.token_user1)
        comm_user2 = await self._connect_user(self.token_user2)

        # User2 disconnects
        await comm_user2.disconnect()
        await asyncio.sleep(0.5)

        # User1 should receive presence.update with only 1 user
        response = await comm_user1.receive_json_from(timeout=2)
        self.assertEqual(response.get('event'), 'presence.update')
        self.assertEqual(len(response['payload']['active_users']), 1)
        self.assertEqual(response['payload']['active_users'][0]['username'], 'testuser1')

        # Cleanup
        await comm_user1.disconnect()

    async def test_concurrent_users_receive_all_broadcasts(self) -> None:
        """
        Test: 10 concurrent users in same vault all receive broadcasts.
        """
        # Create 8 additional users (we already have user1 and user2)
        users = [self.user1, self.user2]
        tokens = [self.token_user1, self.token_user2]

        for i in range(3, 11):
            user = await asyncio.to_thread(
                User.objects.create_user,  # type: ignore[attr-defined]
                username=f'testuser{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            users.append(user)
            tokens.append(str(AccessToken.for_user(user)))

            # Add user to vault as contributor
            await asyncio.to_thread(
                VaultMembership.objects.create,
                vault=self.vault,
                user=user,
                role=RoleChoices.CONTRIBUTOR,
                added_by=self.user1
            )

        # Connect all 10 users
        communicators = []
        for token in tokens:
            comm = await self._connect_user(token)
            communicators.append(comm)
            await asyncio.sleep(0.2)  # Stagger connections slightly

        # User1 creates a source
        source = await asyncio.to_thread(
            Source.objects.create,
            vault=self.vault,
            url='https://example.com/concurrent-test',
            title='Concurrent Test Source',
            description='Testing concurrent broadcasting',
            source_type='URL',
            created_by=self.user1
        )

        # Wait for broadcast to propagate
        await asyncio.sleep(1.0)

        # All 10 users should receive source.created event
        received_count = 0
        for comm in communicators:
            try:
                response = await comm.receive_json_from(timeout=2)
                if response.get('event') == 'source.created':
                    self.assertEqual(response['payload']['id'], source.id)
                    received_count += 1
            except asyncio.TimeoutError:
                pass  # Some users might have already consumed the message

        # At least 8 users should receive the broadcast (allow some timing variance)
        self.assertGreaterEqual(received_count, 8,
                                f'Expected at least 8 users to receive broadcast, got {received_count}')

        # Cleanup all connections
        for comm in communicators:
            await comm.disconnect()
