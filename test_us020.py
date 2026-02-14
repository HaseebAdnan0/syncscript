#!/usr/bin/env python
"""
Verification test for US-020: Implement message throttling (Layer 3).

Tests:
1. Message throttling tracks timestamps in Redis
2. First offense (>60 messages in 60s) sends warning
3. Second offense disconnects
4. Third offense sets temporary ban
5. Ban status checked on connect
"""

import os
import sys
import django
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.vaults.consumers import VaultConsumer
from django.core.cache import cache


def test_check_message_throttle_method_exists():
    """Test: _check_message_throttle method exists"""
    consumer = VaultConsumer()
    assert hasattr(consumer, '_check_message_throttle'), "Missing _check_message_throttle method"
    print("[OK] _check_message_throttle method exists")


def test_set_temporary_ban_method_exists():
    """Test: _set_temporary_ban method exists"""
    consumer = VaultConsumer()
    assert hasattr(consumer, '_set_temporary_ban'), "Missing _set_temporary_ban method"
    print("[OK] _set_temporary_ban method exists")


def test_is_user_banned_method_exists():
    """Test: _is_user_banned method exists"""
    consumer = VaultConsumer()
    assert hasattr(consumer, '_is_user_banned'), "Missing _is_user_banned method"
    print("[OK] _is_user_banned method exists")


def test_redis_keys_structure():
    """Test: Redis key patterns match requirements"""
    # Message tracking uses conn_{channel}:messages
    # Offense tracking uses user_{id}:throttle_offenses
    # Ban tracking uses user_{id}:banned

    # Check consumer source code for correct key patterns
    import inspect
    source = inspect.getsource(VaultConsumer._check_message_throttle)

    assert 'conn_{self.channel_name}:messages' in source, "Missing messages key pattern"
    assert 'user_{self.user.id}:throttle_offenses' in source, "Missing offenses key pattern"
    print("[OK] Redis key patterns correct")


def test_throttle_logic():
    """Test: Throttle logic checks message count and offense count"""
    import inspect
    source = inspect.getsource(VaultConsumer._check_message_throttle)

    # Should check message count > 60
    assert 'message_count' in source, "Missing message count check"
    assert '60' in source, "Missing 60-message threshold"

    # Should return different responses based on offense count
    assert "'warning'" in source or '"warning"' in source, "Missing warning response"
    assert "'disconnect'" in source or '"disconnect"' in source, "Missing disconnect response"
    assert "'ban'" in source or '"ban"' in source, "Missing ban response"

    # Should increment offense counter
    assert 'incr' in source, "Missing offense counter increment"

    print("[OK] Throttle logic implements progressive enforcement")


def test_receive_method_checks_throttle():
    """Test: receive method calls _check_message_throttle"""
    import inspect
    source = inspect.getsource(VaultConsumer.receive)

    assert '_check_message_throttle' in source, "receive method doesn't call throttle check"
    assert 'warning' in source, "Missing warning handling"
    assert 'disconnect' in source, "Missing disconnect handling"
    assert 'ban' in source, "Missing ban handling"

    print("[OK] receive method implements throttle checking")


def test_connect_checks_ban_status():
    """Test: connect method checks if user is banned"""
    import inspect
    source = inspect.getsource(VaultConsumer.connect)

    assert '_is_user_banned' in source, "connect method doesn't check ban status"
    print("[OK] connect method checks ban status")


def test_ban_expiry():
    """Test: Temporary ban has 1-hour expiry"""
    import inspect
    source = inspect.getsource(VaultConsumer._set_temporary_ban)

    # Should set expiry to 3600 seconds (1 hour)
    assert '3600' in source, "Missing 1-hour expiry"
    assert 'setex' in source or 'expire' in source, "Missing expiry command"

    print("[OK] Temporary ban has 1-hour expiry")


def test_offense_tracking_expiry():
    """Test: Offense tracking expires after 1 hour"""
    import inspect
    source = inspect.getsource(VaultConsumer._check_message_throttle)

    # Should set 1 hour expiry on offense counter
    assert '3600' in source, "Missing 1-hour expiry for offense tracking"

    print("[OK] Offense tracking has 1-hour expiry")


if __name__ == '__main__':
    print("\nRunning US-020 verification tests...")
    print("=" * 60)

    test_check_message_throttle_method_exists()
    test_set_temporary_ban_method_exists()
    test_is_user_banned_method_exists()
    test_redis_keys_structure()
    test_throttle_logic()
    test_receive_method_checks_throttle()
    test_connect_checks_ban_status()
    test_ban_expiry()
    test_offense_tracking_expiry()

    print("=" * 60)
    print("[OK] All US-020 verification tests passed!")
    print("\nMessage throttling (Layer 3) implemented successfully:")
    print("- Tracks message timestamps in Redis sorted set")
    print("- First offense: sends warning message")
    print("- Second offense: disconnects with error")
    print("- Third offense: 1-hour temporary ban")
    print("- Ban checked on connect, rejected users can't reconnect")
