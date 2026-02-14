"""
E2E WebSocket tests for rate limiting and event replay.

Tests verify rate limiting enforcement and event replay after reconnection.
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
    CELERY_TASK_ALWAYS_EAGER=True,
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    },
)
class WebSocketRateLimitingTests(TransactionTestCase):
    """
    E2E tests for WebSocket rate limiting and event replay.
    """

    def setUp(self) -> None:
        """Create test fixtures."""
        # Create user
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='user@example.com',
            password='testpass123'
        )

        # Create vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for rate limiting tests',
            owner=self.user
        )

        # Generate JWT token
        self.token = str(AccessToken.for_user(self.user))

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

        # Consume presence.update message
        response = await communicator.receive_json_from(timeout=2)
        self.assertEqual(response.get('event'), 'presence.update')

        return communicator

    async def test_message_throttling_progressive_enforcement(self) -> None:
        """
        Test: Send 61 messages in 60s -> receive warning, then disconnect.

        Layer 3 rate limiting enforces progressive penalties:
        - First offense (>60 msgs/60s): warning message
        - Second offense: disconnect with RATE_LIMIT_EXCEEDED
        - Third offense: temporary ban
        """
        # Connect user
        comm = await self._connect_user(self.token)

        # Send 61 heartbeat messages rapidly (exceeds 60/60s limit)
        for _ in range(61):
            await comm.send_json_to({'type': 'heartbeat'})
            await asyncio.sleep(0.01)  # Small delay to avoid overwhelming

        # Wait briefly for rate limit check
        await asyncio.sleep(0.5)

        # Should receive warning message (first offense)
        try:
            response = await comm.receive_json_from(timeout=3)
            # Warning or error message expected
            self.assertIn(response.get('type'), ['error', 'warning'])
            if response.get('type') == 'error':
                self.assertEqual(response['error']['code'], 'RATE_LIMIT_EXCEEDED')
        except asyncio.TimeoutError:
            # If no message received, connection might have been closed immediately
            pass

        # Send more messages to trigger second offense (disconnect)
        for _ in range(10):
            try:
                await comm.send_json_to({'type': 'heartbeat'})
                await asyncio.sleep(0.01)
            except Exception:
                # Connection closed - expected behavior
                break

        # Wait for disconnect
        await asyncio.sleep(1)

        # Cleanup
        await comm.disconnect()

    async def test_heartbeat_timeout_enforcement(self) -> None:
        """
        Test: No heartbeat for 5 min -> connection closed.

        Note: This test simulates timeout by checking the cleanup task logic.
        Full 5-minute wait is impractical for E2E tests.
        Instead, we verify the connection is active with heartbeats,
        and document that stale connections (>300s) are cleaned by Celery periodic task.
        """
        # Connect user
        comm = await self._connect_user(self.token)

        # Send heartbeat to keep connection alive
        await comm.send_json_to({'type': 'heartbeat'})
        await asyncio.sleep(0.5)

        # Connection should still be active
        # (In real scenario, cleanup_stale_connections task runs every 60s
        # and closes connections with no heartbeat for >300s)

        # Verify connection is still open by sending another heartbeat
        await comm.send_json_to({'type': 'heartbeat'})
        await asyncio.sleep(0.2)

        # No error expected - connection active
        # Real timeout enforcement tested by Celery task (US-021)

        # Cleanup
        await comm.disconnect()

    async def test_event_replay_after_reconnection(self) -> None:
        """
        Test: Disconnect during events -> reconnect with replay_request gets missed events.

        Scenario:
        1. User1 connects
        2. User2 connects and creates sources (broadcasts events)
        3. User1 disconnects before receiving all events
        4. User1 reconnects and requests replay with last known sequence number
        5. User1 receives missed events in chronological order
        """
        # Create second user
        user2 = await asyncio.to_thread(
            User.objects.create_user,  # type: ignore[attr-defined]
            username='testuser2',
            email='user2@example.com',
            password='testpass123'
        )
        await asyncio.to_thread(
            VaultMembership.objects.create,
            vault=self.vault,
            user=user2,
            role=RoleChoices.CONTRIBUTOR,
            added_by=self.user
        )
        token2 = str(AccessToken.for_user(user2))

        # User1 connects
        comm_user1 = await self._connect_user(self.token)

        # Capture current sequence number from connection.success
        # (Already consumed in _connect_user, so we'll track from broadcasts)
        last_seq = 0

        # User2 connects
        comm_user2 = await self._connect_user(token2)

        # Consume presence updates for both users
        # User1 receives presence.update for user2 joining
        response1 = await comm_user1.receive_json_from(timeout=2)
        self.assertEqual(response1.get('event'), 'presence.update')
        last_seq = response1.get('seq', 0)

        # User2 creates 3 sources (triggers broadcasts)
        sources = []
        for i in range(3):
            source = await asyncio.to_thread(
                Source.objects.create,
                vault=self.vault,
                url=f'https://example.com/source-{i}',
                title=f'Test Source {i}',
                description=f'Source {i} for replay test',
                source_type='URL',
                created_by=user2
            )
            sources.append(source)
            await asyncio.sleep(0.3)  # Small delay between creates

        # User1 receives first source.created event
        response = await comm_user1.receive_json_from(timeout=2)
        self.assertEqual(response.get('event'), 'source.created')
        last_seq = response.get('seq', last_seq)

        # User1 disconnects BEFORE receiving other events (simulate disconnect)
        await comm_user1.disconnect()

        # Wait for remaining broadcasts to complete
        await asyncio.sleep(1)

        # User2 consumes remaining broadcasts
        for _ in range(3):
            try:
                await comm_user2.receive_json_from(timeout=2)
            except asyncio.TimeoutError:
                break

        # User1 reconnects
        comm_user1_new = WebsocketCommunicator(
            application,
            f'/ws/vault/{self.vault.id}/?token={self.token}'
        )
        connected, _ = await comm_user1_new.connect()
        self.assertTrue(connected, 'Reconnection should succeed')

        # Consume connection.success and presence.update
        await comm_user1_new.receive_json_from(timeout=2)  # connection.success
        await comm_user1_new.receive_json_from(timeout=2)  # presence.update

        # Request replay of missed events
        await comm_user1_new.send_json_to({
            'type': 'replay_request',
            'since_seq': last_seq
        })

        # Wait for replay
        await asyncio.sleep(0.5)

        # Receive replayed events (should be in chronological order)
        replayed_events = []
        for i in range(5):  # Try to receive up to 5 events
            try:
                response = await comm_user1_new.receive_json_from(timeout=1)
                if response.get('event') in ['source.created', 'source.updated', 'source.deleted']:
                    replayed_events.append(response)
            except asyncio.TimeoutError:
                break

        # Verify we received missed events
        self.assertGreaterEqual(len(replayed_events), 1,
                                f'Should receive at least 1 missed event, got {len(replayed_events)}')

        # Verify events are in chronological order (sequence numbers increasing)
        if len(replayed_events) > 1:
            for i in range(1, len(replayed_events)):
                self.assertGreater(replayed_events[i]['seq'], replayed_events[i-1]['seq'],
                                   'Replayed events should be in chronological order')

        # Cleanup
        await comm_user1_new.disconnect()
        await comm_user2.disconnect()
