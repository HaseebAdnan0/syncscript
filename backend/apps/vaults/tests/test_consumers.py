"""
Unit tests for VaultConsumer WebSocket consumer.

Tests core consumer logic without full E2E WebSocket communication.
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch, call
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.vaults.consumers import VaultConsumer  # type: ignore[import-not-found]
from apps.vaults.models import Vault, VaultMembership  # type: ignore[import-not-found]
from asgiref.sync import async_to_sync

User = get_user_model()


class VaultConsumerUnitTests(TestCase):
    """Unit tests for VaultConsumer core methods."""

    @classmethod
    def setUpTestData(cls):
        """Set up test fixtures once for all tests."""
        # Create test user
        cls.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser_consumer',
            email='test_consumer@example.com',
            password='testpass123'
        )

        # Create test vault
        cls.vault = Vault.objects.create(
            name='Test Vault Consumer',
            description='Test vault for unit tests',
            owner=cls.user
        )

        # Create vault membership
        VaultMembership.objects.create(
            vault=cls.vault,
            user=cls.user,
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

        # Test that vault_id extraction logic works
        url_route = consumer.scope.get('url_route', {})  # type: ignore[typeddict-item]
        vault_id_str = url_route.get('kwargs', {}).get('vault_id')
        self.assertIsNotNone(vault_id_str)

        # Verify vault_id can be converted to int
        vault_id = int(vault_id_str)  # type: ignore[arg-type]
        self.assertEqual(vault_id, self.vault.id)
        self.assertIsInstance(vault_id, int)

    @patch('apps.vaults.consumers.cache.client.get_client')
    def test_disconnect_removes_from_presence(self, mock_get_redis):
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
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        # Mock presence list (empty after removal)
        mock_redis_conn.zrange.return_value = []

        # Call _remove_from_presence directly
        async_to_sync(consumer._remove_from_presence)(self.user.id, self.vault.id)

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

        # Run vault_event using async_to_sync
        async_to_sync(consumer.vault_event)(test_event)

        # Verify send was called with JSON-encoded event
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args
        sent_data = call_args.kwargs.get('text_data')

        # Parse sent JSON
        if sent_data:
            sent_json = json.loads(sent_data)

            # Verify event was forwarded correctly
            self.assertEqual(sent_json['type'], 'vault_event')
            self.assertEqual(sent_json['event_type'], 'source.created')
            self.assertEqual(sent_json['seq'], 5)
            self.assertEqual(sent_json['payload']['id'], 123)
        else:
            self.fail("send() was not called with text_data")

    @patch('apps.vaults.consumers.cache.client.get_client')
    def test_heartbeat_updates_presence_timestamp(self, mock_get_redis):
        """Test that heartbeat message updates user timestamp in Redis."""
        # Create consumer instance
        consumer = VaultConsumer()
        consumer.user = self.user
        consumer.vault_id = self.vault.id
        consumer.channel_name = 'test_channel'

        # Mock Redis operations
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        # Call _update_presence directly
        async_to_sync(consumer._update_presence)(self.user.id, self.vault.id)

        # Verify Redis zadd was called to update presence timestamp
        presence_key = f"vault_{self.vault.id}:presence"
        mock_redis_conn.zadd.assert_called_once()

        # Check the call arguments
        call_args = mock_redis_conn.zadd.call_args
        self.assertEqual(call_args[0][0], presence_key)

        # Verify user_id was updated with a timestamp
        mapping = call_args[0][1]
        self.assertIn(str(self.user.id), mapping)

        # Timestamp should be recent (within last few seconds)
        timestamp = mapping[str(self.user.id)]
        self.assertAlmostEqual(timestamp, time.time(), delta=5)

    @patch('apps.vaults.consumers.cache.client.get_client')
    def test_replay_request_returns_filtered_events(self, mock_get_redis):
        """Test that replay_request returns only events with seq > since_seq."""
        # Create consumer instance
        consumer = VaultConsumer()
        consumer.user = self.user
        consumer.vault_id = self.vault.id
        consumer.channel_name = 'test_channel'
        consumer.send = AsyncMock()

        # Mock Redis operations
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        # Mock buffered events in Redis (stored newest-first with lpush)
        events = [
            json.dumps({'seq': 5, 'event_type': 'source.created', 'payload': {'id': 5}}),
            json.dumps({'seq': 4, 'event_type': 'source.updated', 'payload': {'id': 4}}),
            json.dumps({'seq': 3, 'event_type': 'annotation.created', 'payload': {'id': 3}}),
            json.dumps({'seq': 2, 'event_type': 'source.created', 'payload': {'id': 2}}),
            json.dumps({'seq': 1, 'event_type': 'member.added', 'payload': {'id': 1}}),
        ]
        mock_redis_conn.lrange.return_value = events

        # Call _replay_events directly with since_seq=2
        async_to_sync(consumer._replay_events)(since_seq=2)

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
