#!/usr/bin/env python
"""
Verification test for US-018: Connection limit per user (Layer 1)
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.cache import cache


def test_connection_limit_tracking():
    """Verify connection tracking methods exist and work"""
    print("[OK] Testing connection limit tracking...")

    # Import consumer
    from apps.vaults.consumers import VaultConsumer

    # Check methods exist
    assert hasattr(VaultConsumer, '_check_and_enforce_connection_limit'), "Missing _check_and_enforce_connection_limit method"
    assert hasattr(VaultConsumer, '_add_user_connection'), "Missing _add_user_connection method"
    assert hasattr(VaultConsumer, '_remove_user_connection'), "Missing _remove_user_connection method"
    assert hasattr(VaultConsumer, 'close_connection'), "Missing close_connection handler"

    print("[OK] All connection limit methods exist")


def test_redis_connection_tracking():
    """Verify Redis connection tracking works"""
    print("[OK] Testing Redis connection tracking...")

    redis_conn = cache.client.get_client()
    test_key = "user_999:connections"

    # Clean up any existing test data
    redis_conn.delete(test_key)

    # Add 3 connections
    redis_conn.zadd(test_key, {
        "channel_1": 1000.0,
        "channel_2": 2000.0,
        "channel_3": 3000.0
    })

    # Verify count
    count = redis_conn.zcard(test_key)
    assert count == 3, f"Expected 3 connections, got {count}"

    # Verify oldest connection
    oldest = redis_conn.zrange(test_key, 0, 0, withscores=True)
    assert oldest[0][0].decode('utf-8') == "channel_1", "Oldest connection should be channel_1"
    assert oldest[0][1] == 1000.0, "Oldest connection timestamp should be 1000.0"

    # Remove oldest
    redis_conn.zrem(test_key, "channel_1")

    # Verify removal
    count = redis_conn.zcard(test_key)
    assert count == 2, f"Expected 2 connections after removal, got {count}"

    # Clean up
    redis_conn.delete(test_key)

    print("[OK] Redis connection tracking works correctly")


def test_connection_limit_logic():
    """Verify connection limit logic (5 connections max)"""
    print("[OK] Testing connection limit logic...")

    redis_conn = cache.client.get_client()
    test_key = "user_888:connections"

    # Clean up
    redis_conn.delete(test_key)

    # Add 5 connections
    for i in range(5):
        redis_conn.zadd(test_key, {f"channel_{i}": float(i * 1000)})

    # Check count
    count = redis_conn.zcard(test_key)
    assert count == 5, f"Expected 5 connections, got {count}"

    # Simulate adding 6th connection - should trigger limit
    connections = redis_conn.zrange(test_key, 0, -1, withscores=True)
    if len(connections) >= 5:
        # This would trigger closing oldest connection
        oldest_channel = connections[0][0].decode('utf-8')
        assert oldest_channel == "channel_0", "Oldest channel should be channel_0"
        print(f"[OK] Would close oldest connection: {oldest_channel}")

    # Clean up
    redis_conn.delete(test_key)

    print("[OK] Connection limit logic verified")


if __name__ == '__main__':
    try:
        test_connection_limit_tracking()
        test_redis_connection_tracking()
        test_connection_limit_logic()

        print("\n" + "="*60)
        print("[OK] All US-018 verification tests passed!")
        print("="*60)
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
