"""
Test script to verify broadcast_to_vault utility function.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.websocket_utils import broadcast_to_vault
from django.core.cache import cache

# Test 1: Verify function imports successfully
print("[OK] broadcast_to_vault imported successfully")

# Test 2: Verify sequence number increments in Redis
vault_id = 999
redis_client = cache.client.get_client()  # type: ignore[attr-defined]
seq_key = f"vault_{vault_id}:seq"

# Clear any existing sequence
redis_client.delete(seq_key)

# First broadcast should create seq=1
broadcast_to_vault(
    vault_id=vault_id,
    event_type="source.created",
    payload={"source_id": 123, "title": "Test Source"},
    user=None,
)

seq1 = redis_client.get(seq_key)
assert seq1 is not None, "Sequence number should exist"
assert int(seq1) == 1, f"First sequence should be 1, got {seq1}"
print(f"[OK] First broadcast created sequence number: {seq1}")

# Second broadcast should increment to seq=2
broadcast_to_vault(
    vault_id=vault_id,
    event_type="annotation.created",
    payload={"annotation_id": 456, "text": "Test annotation"},
    user=None,
)

seq2 = redis_client.get(seq_key)
assert seq2 is not None, "Sequence number should exist"
assert int(seq2) == 2, f"Second sequence should be 2, got {seq2}"
print(f"[OK] Second broadcast incremented sequence to: {seq2}")

# Test 3: Verify function doesn't crash with user object
class MockUser:
    id = 42
    username = "testuser"

broadcast_to_vault(
    vault_id=vault_id,
    event_type="source.updated",
    payload={"source_id": 789},
    user=MockUser(),
)

seq3 = redis_client.get(seq_key)
assert int(seq3) == 3, f"Third sequence should be 3, got {seq3}"
print(f"[OK] Broadcast with user object succeeded, sequence: {seq3}")

# Cleanup
redis_client.delete(seq_key)

print("\n[SUCCESS] All broadcast_to_vault tests passed!")
