#!/usr/bin/env python
"""
Verification script for US-021: Heartbeat timeout enforcement (Layer 4)

Tests:
1. cleanup_stale_connections task exists in apps/vaults/tasks.py
2. Task is registered in Celery beat schedule with 60s interval
3. Task scans presence sets and disconnects stale connections
4. Consumer close_connection handler supports idle timeout
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_cleanup_task_exists():
    """Test that cleanup_stale_connections task is defined"""
    from apps.vaults import tasks

    assert hasattr(tasks, 'cleanup_stale_connections'), \
        "cleanup_stale_connections task not found in apps.vaults.tasks"

    # Verify it's a Celery task
    task_fn = tasks.cleanup_stale_connections
    assert hasattr(task_fn, 'delay'), \
        "cleanup_stale_connections is not a Celery task (no .delay method)"

    print("[OK] cleanup_stale_connections task exists")

def test_celery_beat_schedule():
    """Test that periodic task is configured in Celery Beat"""
    from config.celery import app

    beat_schedule = app.conf.beat_schedule

    assert 'cleanup-stale-websocket-connections' in beat_schedule, \
        "cleanup-stale-websocket-connections not found in beat_schedule"

    task_config = beat_schedule['cleanup-stale-websocket-connections']

    assert task_config['task'] == 'apps.vaults.tasks.cleanup_stale_connections', \
        f"Wrong task path: {task_config['task']}"

    assert task_config['schedule'] == 60.0, \
        f"Wrong schedule interval: {task_config['schedule']} (expected 60.0)"

    print("[OK] Celery Beat schedule configured (60s interval)")

def test_task_implementation():
    """Test that cleanup task has correct implementation"""
    import inspect
    from apps.vaults.tasks import cleanup_stale_connections

    # Check function signature
    sig = inspect.signature(cleanup_stale_connections)
    assert len(sig.parameters) == 0, \
        "cleanup_stale_connections should take no parameters"

    # Check source code for key operations
    source = inspect.getsource(cleanup_stale_connections)

    # Verify presence key scanning
    assert "vault_*:presence" in source, \
        "Task should scan for vault_*:presence keys"

    # Verify timeout threshold (300 seconds)
    assert "300" in source, \
        "Task should use 300 second timeout threshold"

    # Verify stale user detection
    assert "zrangebyscore" in source or "zrange" in source, \
        "Task should query Redis sorted set for stale entries"

    # Verify close_connection message
    assert "close_connection" in source, \
        "Task should send close_connection messages"

    # Verify presence removal
    assert "zrem" in source, \
        "Task should remove stale users from presence set"

    print("[OK] Task implementation includes all required operations")

def test_consumer_close_handler_updated():
    """Test that close_connection handler supports idle timeout"""
    import inspect
    from apps.vaults.consumers import VaultConsumer

    # Check that close_connection method exists
    assert hasattr(VaultConsumer, 'close_connection'), \
        "VaultConsumer missing close_connection method"

    # Check source code for reason parameter support
    source = inspect.getsource(VaultConsumer.close_connection)

    assert "'reason'" in source or '"reason"' in source, \
        "close_connection should handle 'reason' parameter from event"

    assert "IDLE_TIMEOUT" in source, \
        "close_connection should support IDLE_TIMEOUT error code"

    assert "1000" in source, \
        "close_connection should handle code 1000 (normal closure)"

    print("[OK] Consumer close_connection handler supports idle timeout")

def main():
    """Run all verification tests"""
    print("Verifying US-021: Heartbeat timeout enforcement (Layer 4)\n")

    try:
        test_cleanup_task_exists()
        test_celery_beat_schedule()
        test_task_implementation()
        test_consumer_close_handler_updated()

        print("\n" + "="*60)
        print("All US-021 tests passed!")
        print("="*60)

    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
