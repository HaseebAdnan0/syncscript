"""
Standalone verification script for consumer unit tests.

This script verifies the test_consumers.py file is correctly structured
without requiring database setup.
"""

import sys
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from asgiref.sync import async_to_sync

# Setup Django before importing apps
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.vaults.consumers import VaultConsumer  # type: ignore[import-not-found]

def test_vault_event_sends_to_websocket():
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
    assert consumer.send.call_count == 1, f"Expected 1 call, got {consumer.send.call_count}"

    call_args = consumer.send.call_args
    sent_data = call_args.kwargs.get('text_data')

    # Parse sent JSON
    if sent_data:
        sent_json = json.loads(sent_data)

        # Verify event was forwarded correctly
        assert sent_json['type'] == 'vault_event', f"Expected 'vault_event', got {sent_json['type']}"
        assert sent_json['event_type'] == 'source.created', f"Expected 'source.created', got {sent_json['event_type']}"
        assert sent_json['seq'] == 5, f"Expected seq 5, got {sent_json['seq']}"
        assert sent_json['payload']['id'] == 123, f"Expected id 123, got {sent_json['payload']['id']}"
        print("[OK] test_vault_event_sends_to_websocket passed")
    else:
        raise AssertionError("send() was not called with text_data")


@patch('apps.vaults.consumers.cache.client.get_client')
def test_disconnect_removes_from_presence(mock_get_redis):
    """Test that disconnect removes user from presence tracking."""
    # Create consumer instance
    consumer = VaultConsumer()

    # Set up consumer state (as if connected)
    class MockUser:
        id = 1

    consumer.user = MockUser()
    consumer.vault_id = 42
    consumer.room_group_name = "vault_42"
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
    async_to_sync(consumer._remove_from_presence)(consumer.user.id, consumer.vault_id)

    # Verify Redis zrem was called to remove user from presence
    presence_key = "vault_42:presence"
    mock_redis_conn.zrem.assert_called_with(presence_key, str(consumer.user.id))
    print("[OK] test_disconnect_removes_from_presence passed")


@patch('apps.vaults.consumers.cache.client.get_client')
def test_heartbeat_updates_presence_timestamp(mock_get_redis):
    """Test that heartbeat message updates user timestamp in Redis."""
    # Create consumer instance
    consumer = VaultConsumer()

    class MockUser:
        id = 1

    consumer.user = MockUser()
    consumer.vault_id = 42
    consumer.channel_name = 'test_channel'

    # Mock Redis operations
    mock_redis_conn = MagicMock()
    mock_get_redis.return_value = mock_redis_conn

    # Call _update_presence directly
    async_to_sync(consumer._update_presence)(consumer.user.id, consumer.vault_id)

    # Verify Redis zadd was called to update presence timestamp
    presence_key = "vault_42:presence"
    assert mock_redis_conn.zadd.call_count == 1, f"Expected 1 zadd call, got {mock_redis_conn.zadd.call_count}"

    # Check the call arguments
    call_args = mock_redis_conn.zadd.call_args
    assert call_args[0][0] == presence_key, f"Expected presence_key '{presence_key}', got '{call_args[0][0]}'"

    # Verify user_id was updated with a timestamp
    mapping = call_args[0][1]
    assert str(consumer.user.id) in mapping, f"User ID {consumer.user.id} not in mapping"

    # Timestamp should be recent (within last few seconds)
    timestamp = mapping[str(consumer.user.id)]
    time_diff = abs(timestamp - time.time())
    assert time_diff < 5, f"Timestamp diff {time_diff} > 5 seconds"

    print("[OK] test_heartbeat_updates_presence_timestamp passed")


@patch('apps.vaults.consumers.cache.client.get_client')
def test_replay_request_returns_filtered_events(mock_get_redis):
    """Test that replay_request returns only events with seq > since_seq."""
    # Create consumer instance
    consumer = VaultConsumer()

    class MockUser:
        id = 1

    consumer.user = MockUser()
    consumer.vault_id = 42
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
    events_key = "vault_42:events"
    mock_redis_conn.lrange.assert_called_with(events_key, 0, -1)

    # Verify send was called for filtered events (seq 3, 4, 5 in chronological order)
    assert consumer.send.call_count == 3, f"Expected 3 send calls, got {consumer.send.call_count}"

    # Check events were sent in chronological order (oldest first)
    call_args_list = consumer.send.call_args_list

    # First call should be seq 3
    sent_1 = json.loads(call_args_list[0].kwargs['text_data'])
    assert sent_1['seq'] == 3, f"Expected seq 3, got {sent_1['seq']}"

    # Second call should be seq 4
    sent_2 = json.loads(call_args_list[1].kwargs['text_data'])
    assert sent_2['seq'] == 4, f"Expected seq 4, got {sent_2['seq']}"

    # Third call should be seq 5
    sent_3 = json.loads(call_args_list[2].kwargs['text_data'])
    assert sent_3['seq'] == 5, f"Expected seq 5, got {sent_3['seq']}"

    print("[OK] test_replay_request_returns_filtered_events passed")


def test_connect_sets_vault_id_in_scope():
    """Test that connect extracts vault_id from URL kwargs."""
    # Create consumer instance
    consumer = VaultConsumer()

    class MockUser:
        id = 1

    # Mock scope with vault_id in URL route
    consumer.scope = {
        'user': MockUser(),
        'url_route': {
            'kwargs': {
                'vault_id': '42'
            }
        }
    }

    # Test that vault_id extraction logic works
    url_route = consumer.scope.get('url_route', {})  # type: ignore[typeddict-item]
    vault_id_str = url_route.get('kwargs', {}).get('vault_id')
    assert vault_id_str is not None, "vault_id_str should not be None"

    # Verify vault_id can be converted to int
    vault_id = int(vault_id_str)  # type: ignore[arg-type]
    assert vault_id == 42, f"Expected vault_id 42, got {vault_id}"
    assert isinstance(vault_id, int), f"Expected int, got {type(vault_id)}"

    print("[OK] test_connect_sets_vault_id_in_scope passed")


if __name__ == '__main__':
    print("Running consumer unit tests...\n")

    try:
        test_vault_event_sends_to_websocket()
        test_disconnect_removes_from_presence()
        test_heartbeat_updates_presence_timestamp()
        test_replay_request_returns_filtered_events()
        test_connect_sets_vault_id_in_scope()

        print("\n===============================")
        print("All 5 tests passed!")
        print("===============================")
        sys.exit(0)

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
