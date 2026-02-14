#!/usr/bin/env python
"""
Test script to verify heartbeat handling in VaultConsumer.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import json
import time
from unittest.mock import MagicMock, AsyncMock, patch
from apps.vaults.consumers import VaultConsumer

async def test_heartbeat_updates_presence():
    """Test that heartbeat messages update presence timestamp."""
    consumer = VaultConsumer()

    # Mock the necessary attributes
    consumer.user = MagicMock()
    consumer.user.id = 123
    consumer.vault_id = 456
    consumer._update_presence = AsyncMock()

    # Test heartbeat message
    heartbeat_msg = json.dumps({"type": "heartbeat"})
    await consumer.receive(text_data=heartbeat_msg)

    # Verify _update_presence was called with correct arguments
    consumer._update_presence.assert_called_once_with(123, 456)
    print("[OK] Heartbeat updates presence timestamp")

async def test_receive_handles_unknown_type():
    """Test that unknown message types are logged but don't crash."""
    consumer = VaultConsumer()
    consumer.user = MagicMock()
    consumer.user.id = 123
    consumer.vault_id = 456

    # Test unknown message type
    unknown_msg = json.dumps({"type": "unknown_type"})

    with patch('apps.vaults.consumers.logger') as mock_logger:
        await consumer.receive(text_data=unknown_msg)
        mock_logger.warning.assert_called_once()
        print("[OK] Unknown message types logged correctly")

async def test_receive_handles_invalid_json():
    """Test that invalid JSON is handled gracefully."""
    consumer = VaultConsumer()

    # Test invalid JSON
    invalid_json = "not valid json"

    with patch('apps.vaults.consumers.logger') as mock_logger:
        await consumer.receive(text_data=invalid_json)
        mock_logger.error.assert_called_once()
        print("[OK] Invalid JSON handled gracefully")

async def test_receive_handles_none():
    """Test that None text_data is handled gracefully."""
    consumer = VaultConsumer()

    # Should return early without error
    await consumer.receive(text_data=None)
    print("[OK] None text_data handled gracefully")

async def main():
    """Run all tests."""
    print("Testing heartbeat handling...")
    print()

    await test_heartbeat_updates_presence()
    await test_receive_handles_unknown_type()
    await test_receive_handles_invalid_json()
    await test_receive_handles_none()

    print()
    print("All tests passed! [SUCCESS]")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
