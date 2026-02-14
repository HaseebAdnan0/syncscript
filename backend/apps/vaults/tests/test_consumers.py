"""
Unit tests for VaultConsumer WebSocket consumer.

Tests core consumer logic without full E2E WebSocket communication.
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from apps.vaults.consumers import VaultConsumer
from apps.vaults.models import Vault, VaultMembership

User = get_user_model()


class VaultConsumerUnitTests(TestCase):
    """Unit tests for VaultConsumer core methods."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for unit tests',
            owner=self.user
        )

        # Create vault membership
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.user,
            role='OWNER'
        )

    def test_connect_sets_vault_id_in_scope(self):
        """Test that connect extracts and stores vault_id from URL kwargs."""
        # Create consumer instance
        consumer = VaultConsumer()

        # Mock scope with vault_id in URL route
        consumer.scope = {
            'user': self.user,
            'url_route': {
                'kwargs': {
                    'vault_id': str(self.vault.id)
                }
            }
        }

        # Mock methods to prevent actual WebSocket operations
        consumer.accept = AsyncMock()
        consumer.send = AsyncMock()
        consumer.channel_layer = MagicMock()
        consumer.channel_layer.group_add = AsyncMock()
        consumer.channel_name = 'test_channel'

        # Mock Redis operations
        with patch('apps.vaults.consumers.cache.client.get_client') as mock_redis:
            mock_redis_conn = MagicMock()
            mock_redis.return_value = mock_redis_conn

            # Mock Redis responses
            mock_redis_conn.zrange.return_value = []  # No existing connections
            mock_redis_conn.zcard.return_value = 0  # No room members
            mock_redis_conn.exists.return_value = False  # User not banned

            # Run connect
            import asyncio
            asyncio.run(consumer.connect())

        # Verify vault_id was set
        self.assertEqual(consumer.vault_id, self.vault.id)
        self.assertIsInstance(consumer.vault_id, int)

    def test_disconnect_removes_from_presence(self):
        """Test that disconnect removes user from presence tracking."""
        # Create consumer instance
        consumer = VaultConsumer()

        # Set up consumer state (as if connected)
        consumer.user = self.user
        consumer.vault_id = self.vault.id
        consumer.room_group_name = f"vault_{self.vault.id}"
        consumer.channel_name = 'test_channel'
        consumer.channel_layer = MagicMock()
        consumer.channel_layer.group_discard = AsyncMock()
        consumer.channel_layer.group_send = AsyncMock()

        # Mock Redis operations
        with patch('apps.vaults.consumers.cache.client.get_client') as mock_redis:
            mock_redis_conn = MagicMock()
            mock_redis.return_value = mock_redis_conn

            # Mock presence list (empty after removal)
            mock_redis_conn.zrange.return_value = []

            # Run disconnect
            import asyncio
            asyncio.run(consumer.disconnect(code=1000))

            # Verify Redis zrem was called to remove user from presence
            presence_key = f"vault_{self.vault.id}:presence"
            mock_redis_conn.zrem.assert_called_with(presence_key, str(self.user.id))

    def test_vault_event_sends_to_websocket(self):
        """Test that vault_event forwards channel layer messages to WebSocket."""
        # Create consumer instance
        consumer = VaultConsumer()
        consumer.send = AsyncMock()

        # Test event from channel layer
        test_event = {
            'type': 'vault_event',
            'event_type': 'source.created',
            'payload': {
                'id': 123,
                'title': 'Test Source'
            },
            'seq': 5
        }

        # Run vault_event
        import asyncio
        asyncio.run(consumer.vault_event(test_event))

        # Verify send was called with JSON-encoded event
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args
        sent_data = call_args.kwargs.get('text_data')

        # Parse sent JSON
        sent_json = json.loads(sent_data)

        # Verify event was forwarded correctly
        self.assertEqual(sent_json['type'], 'vault_event')
        self.assertEqual(sent_json['event_type'], 'source.created')
        self.assertEqual(sent_json['seq'], 5)
        self.assertEqual(sent_json['payload']['id'], 123)

    def test_heartbeat_updates_presence_timestamp(self):
        """Test that heartbeat message updates user timestamp in Redis."""
        # Create consumer instance
        consumer = VaultConsumer()
        consumer.user = self.user
        consumer.vault_id = self.vault.id
        consumer.channel_name = 'test_channel'

        # Mock Redis operations
        with patch('apps.vaults.consumers.cache.client.get_client') as mock_redis:
            mock_redis_conn = MagicMock()
            mock_redis.return_value = mock_redis_conn

            # Mock message throttle check to return 'ok'
            mock_redis_conn.zadd = MagicMock()
            mock_redis_conn.zcard.return_value = 1  # Within throttle limit
            mock_redis_conn.zremrangebyscore = MagicMock()
            mock_redis_conn.expire = MagicMock()

            # Heartbeat message
            heartbeat_msg = json.dumps({'type': 'heartbeat'})

            # Run receive
            import asyncio
            asyncio.run(consumer.receive(text_data=heartbeat_msg))

            # Verify Redis zadd was called to update presence timestamp
            presence_key = f"vault_{self.vault.id}:presence"
            calls = mock_redis_conn.zadd.call_args_list

            # Find the call for presence update (not message throttle)
            presence_updated = False
            for call in calls:
                if call[0][0] == presence_key:
                    # Verify user_id was updated with a timestamp
                    mapping = call[0][1]
                    self.assertIn(str(self.user.id), mapping)
                    # Timestamp should be recent (within last few seconds)
                    timestamp = mapping[str(self.user.id)]
                    self.assertAlmostEqual(timestamp, time.time(), delta=5)
                    presence_updated = True
                    break

            self.assertTrue(presence_updated, "Presence timestamp was not updated")

    def test_replay_request_returns_filtered_events(self):
        """Test that replay_request returns only events with seq > since_seq."""
        # Create consumer instance
        consumer = VaultConsumer()
        consumer.user = self.user
        consumer.vault_id = self.vault.id
        consumer.channel_name = 'test_channel'
        consumer.send = AsyncMock()

        # Mock Redis operations
        with patch('apps.vaults.consumers.cache.client.get_client') as mock_redis:
            mock_redis_conn = MagicMock()
            mock_redis.return_value = mock_redis_conn

            # Mock message throttle check to return 'ok'
            mock_redis_conn.zcard.return_value = 1  # Within throttle limit
            mock_redis_conn.zremrangebyscore = MagicMock()
            mock_redis_conn.expire = MagicMock()

            # Mock buffered events in Redis (stored newest-first with lpush)
            events = [
                json.dumps({'seq': 5, 'event_type': 'source.created', 'payload': {'id': 5}}),
                json.dumps({'seq': 4, 'event_type': 'source.updated', 'payload': {'id': 4}}),
                json.dumps({'seq': 3, 'event_type': 'annotation.created', 'payload': {'id': 3}}),
                json.dumps({'seq': 2, 'event_type': 'source.created', 'payload': {'id': 2}}),
                json.dumps({'seq': 1, 'event_type': 'member.added', 'payload': {'id': 1}}),
            ]
            mock_redis_conn.lrange.return_value = events

            # Replay request message (request events since seq 2)
            replay_msg = json.dumps({'type': 'replay_request', 'since_seq': 2})

            # Run receive
            import asyncio
            asyncio.run(consumer.receive(text_data=replay_msg))

            # Verify lrange was called to fetch events
            events_key = f"vault_{self.vault.id}:events"
            mock_redis_conn.lrange.assert_called_with(events_key, 0, -1)

            # Verify send was called for filtered events (seq 3, 4, 5 in chronological order)
            self.assertEqual(consumer.send.call_count, 3)

            # Check events were sent in chronological order (oldest first)
            call_args_list = consumer.send.call_args_list

            # First call should be seq 3
            sent_1 = json.loads(call_args_list[0].kwargs['text_data'])
            self.assertEqual(sent_1['seq'], 3)

            # Second call should be seq 4
            sent_2 = json.loads(call_args_list[1].kwargs['text_data'])
            self.assertEqual(sent_2['seq'], 4)

            # Third call should be seq 5
            sent_3 = json.loads(call_args_list[2].kwargs['text_data'])
            self.assertEqual(sent_3['seq'], 5)
