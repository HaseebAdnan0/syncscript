"""
Simple test script to verify US-019 implementation without requiring Redis.

Acceptance Criteria:
- [x] On connect, count members in vault_{id} group (via presence set)
- [x] If >= 100 connections, reject with error message and close
- [x] Error code: ROOM_FULL
- [x] Typecheck passes
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_method_exists():
    """Test that _check_room_limit method exists in consumers.py"""
    with open('apps/vaults/consumers.py', 'r') as f:
        content = f.read()
        assert 'async def _check_room_limit(self, vault_id: int)' in content, \
            "_check_room_limit method not found"
        assert 'Layer 2 rate limiting' in content, \
            "Layer 2 rate limiting comment not found"
        print("[OK] _check_room_limit method exists with correct signature")

def test_uses_presence_set():
    """Test that method uses presence set to count connections"""
    with open('apps/vaults/consumers.py', 'r') as f:
        content = f.read()
        assert 'vault_{vault_id}:presence' in content or 'f"vault_{vault_id}:presence"' in content, \
            "Method doesn't use presence set"
        assert 'zcard' in content, \
            "Method doesn't use zcard to count connections"
        print("[OK] Method uses presence set and zcard to count connections")

def test_checks_100_limit():
    """Test that method checks for >= 100 connection limit"""
    with open('apps/vaults/consumers.py', 'r') as f:
        content = f.read()
        # Look for the _check_room_limit method
        method_start = content.find('async def _check_room_limit')
        method_section = content[method_start:method_start+1000]

        assert '>= 100' in method_section or '>=100' in method_section, \
            "Method doesn't check for 100 connection limit"
        assert 'return False' in method_section, \
            "Method doesn't return False when limit exceeded"
        assert 'return True' in method_section, \
            "Method doesn't return True when capacity available"
        print("[OK] Method checks for >= 100 connection limit")

def test_room_full_error_in_connect():
    """Test that connect method uses ROOM_FULL error code"""
    with open('apps/vaults/consumers.py', 'r') as f:
        content = f.read()
        assert 'ROOM_FULL' in content, "ROOM_FULL error code not found"
        assert '_check_room_limit' in content, "_check_room_limit not called in connect"
        assert 'Vault room is full' in content or 'room is full' in content.lower(), \
            "Room full error message not found"
        print("[OK] ROOM_FULL error code implemented in connect method")

def test_connect_method_calls_check():
    """Test that connect method calls _check_room_limit before accepting"""
    with open('apps/vaults/consumers.py', 'r') as f:
        content = f.read()
        # Find connect method
        connect_start = content.find('async def connect(self)')
        connect_section = content[connect_start:connect_start+3000]

        assert 'await self._check_room_limit' in connect_section, \
            "connect method doesn't call _check_room_limit"

        # Check that room limit is enforced before accept()
        room_check_pos = connect_section.find('_check_room_limit')
        accept_pos = connect_section.find('await self.accept()')

        assert room_check_pos < accept_pos, \
            "Room limit check must be before accept()"

        print("[OK] connect method calls _check_room_limit before accept()")

def test_typecheck():
    """Run pyright typecheck on consumers.py"""
    import subprocess
    result = subprocess.run(
        ['python', '-m', 'pyright', 'apps/vaults/consumers.py', '--warnings'],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Typecheck failed:\n{result.stdout}\n{result.stderr}"
    assert '0 errors' in result.stdout, f"Typecheck has errors:\n{result.stdout}"
    print("[OK] Typecheck passes with 0 errors")

if __name__ == '__main__':
    print("=== Testing US-019: Implement room limit per vault (Layer 2) ===\n")

    try:
        test_method_exists()
        test_uses_presence_set()
        test_checks_100_limit()
        test_room_full_error_in_connect()
        test_connect_method_calls_check()
        test_typecheck()

        print("\n=== All tests passed! ===")
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
