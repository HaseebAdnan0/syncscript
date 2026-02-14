"""
Test script to verify US-019: Implement room limit per vault (Layer 2)

Acceptance Criteria:
- [x] On connect, count members in vault_{id} group (via presence set)
- [x] If >= 100 connections, reject with error message and close
- [x] Error code: ROOM_FULL
- [x] Typecheck passes
"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.vaults.consumers import VaultConsumer
from django.core.cache import cache
import asyncio

def test_check_room_limit_method_exists():
    """Test that _check_room_limit method exists on VaultConsumer"""
    assert hasattr(VaultConsumer, '_check_room_limit'), "_check_room_limit method not found"
    print("[OK] _check_room_limit method exists on VaultConsumer")

async def test_check_room_limit_allows_connection():
    """Test that _check_room_limit returns True when room has capacity"""
    consumer = VaultConsumer()
    vault_id = 999  # Use a test vault ID

    # Clear any existing presence data
    redis_conn = cache.client.get_client()  # type: ignore[attr-defined]
    redis_conn.delete(f"vault_{vault_id}:presence")

    # Add 50 users to presence (below limit)
    for i in range(50):
        redis_conn.zadd(f"vault_{vault_id}:presence", {f"user_{i}": 1000000000.0})

    result = await consumer._check_room_limit(vault_id)
    assert result == True, f"Expected True, got {result}"

    # Cleanup
    redis_conn.delete(f"vault_{vault_id}:presence")

    print("[OK] Room limit allows connection when under 100")

async def test_check_room_limit_rejects_when_full():
    """Test that _check_room_limit returns False when room is full (>= 100)"""
    consumer = VaultConsumer()
    vault_id = 998  # Use a different test vault ID

    # Clear any existing presence data
    redis_conn = cache.client.get_client()  # type: ignore[attr-defined]
    redis_conn.delete(f"vault_{vault_id}:presence")

    # Add 100 users to presence (at limit)
    for i in range(100):
        redis_conn.zadd(f"vault_{vault_id}:presence", {f"user_{i}": 1000000000.0})

    result = await consumer._check_room_limit(vault_id)
    assert result == False, f"Expected False, got {result}"

    # Cleanup
    redis_conn.delete(f"vault_{vault_id}:presence")

    print("[OK] Room limit rejects connection when at 100")

async def test_check_room_limit_at_99():
    """Test that _check_room_limit allows connection at 99 (just under limit)"""
    consumer = VaultConsumer()
    vault_id = 997

    # Clear any existing presence data
    redis_conn = cache.client.get_client()  # type: ignore[attr-defined]
    redis_conn.delete(f"vault_{vault_id}:presence")

    # Add 99 users to presence (just under limit)
    for i in range(99):
        redis_conn.zadd(f"vault_{vault_id}:presence", {f"user_{i}": 1000000000.0})

    result = await consumer._check_room_limit(vault_id)
    assert result == True, f"Expected True for 99 connections, got {result}"

    # Cleanup
    redis_conn.delete(f"vault_{vault_id}:presence")

    print("[OK] Room limit allows connection at 99 (just under limit)")

async def test_room_full_error_code():
    """Test that connect method uses ROOM_FULL error code"""
    # Check the code by reading the consumers.py file
    with open('apps/vaults/consumers.py', 'r') as f:
        content = f.read()
        assert 'ROOM_FULL' in content, "ROOM_FULL error code not found"
        assert 'Vault room is full' in content, "Room full error message not found"

    print("[OK] ROOM_FULL error code implemented in connect method")

if __name__ == '__main__':
    print("=== Testing US-019: Implement room limit per vault (Layer 2) ===\n")

    try:
        # Sync tests
        test_check_room_limit_method_exists()
        test_room_full_error_code()

        # Async tests
        asyncio.run(test_check_room_limit_allows_connection())
        asyncio.run(test_check_room_limit_rejects_when_full())
        asyncio.run(test_check_room_limit_at_99())

        print("\n=== All tests passed! ===")
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
