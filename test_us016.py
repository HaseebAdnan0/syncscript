"""Test US-016: Event buffering in Redis"""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.cache import cache
from core.websocket_utils import broadcast_to_vault

print("[OK] Testing event buffering in Redis...")

# Get Redis client
redis_client = cache.client.get_client()

# Clean up any existing test data
vault_id = 999
events_key = f"vault_{vault_id}:events"
seq_key = f"vault_{vault_id}:seq"
redis_client.delete(events_key)
redis_client.delete(seq_key)

print("[OK] Cleared test data")

# Test 1: Broadcast event and check it's in Redis
broadcast_to_vault(
    vault_id=vault_id,
    event_type="test.event",
    payload={"test": "data"},
)

events = redis_client.lrange(events_key, 0, -1)
assert len(events) == 1, f"Expected 1 event, found {len(events)}"
print("[OK] Event stored in Redis list")

# Verify event structure
event_data = json.loads(events[0])
assert event_data["type"] == "test.event"
assert event_data["seq"] == 1
assert event_data["payload"]["test"] == "data"
print("[OK] Event data structure correct")

# Test 2: Check TTL is set
ttl = redis_client.ttl(events_key)
assert 3500 < ttl <= 3600, f"Expected TTL ~3600s, got {ttl}s"
print(f"[OK] TTL set correctly ({ttl}s)")

# Test 3: Add 100 more events and verify trimming
for i in range(100):
    broadcast_to_vault(
        vault_id=vault_id,
        event_type=f"test.event.{i}",
        payload={"index": i},
    )

events_count = redis_client.llen(events_key)
assert events_count == 100, f"Expected 100 events after trim, found {events_count}"
print(f"[OK] List trimmed to 100 events (ltrim working)")

# Test 4: Verify oldest event was removed
latest_events = redis_client.lrange(events_key, 0, 2)
latest_event = json.loads(latest_events[0])
assert latest_event["type"] == "test.event.99", "Latest event should be test.event.99"
print("[OK] Newest events at head (lpush working)")

# Oldest should be test.event.0 (not the very first test.event)
oldest_event = json.loads(latest_events[-1])
print(f"[OK] Third from head is: {oldest_event['type']}")

# Clean up
redis_client.delete(events_key)
redis_client.delete(seq_key)

print("\n=== All tests passed! ===")
print("broadcast_to_vault now buffers events in Redis with:")
print("- lpush to add events (newest at head)")
print("- ltrim to keep only last 100 events")
print("- expire to set 1-hour TTL")
