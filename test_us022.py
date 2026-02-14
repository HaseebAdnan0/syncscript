"""
Verification script for US-022: Error message format and close handling
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import inspect
from apps.vaults.consumers import VaultConsumer

def test_send_error_method_exists():
    """Test that _send_error_and_close method exists."""
    assert hasattr(VaultConsumer, '_send_error_and_close'), "_send_error_and_close method not found"
    print("[OK] _send_error_and_close method exists")

def test_send_error_signature():
    """Test that method has correct signature with details parameter."""
    method = getattr(VaultConsumer, '_send_error_and_close')
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())

    assert 'code' in params, "Missing 'code' parameter"
    assert 'message' in params, "Missing 'message' parameter"
    assert 'details' in params, "Missing 'details' parameter"

    # Check details is optional (has default)
    assert sig.parameters['details'].default is not inspect.Parameter.empty, "details parameter should be optional"

    print("[OK] Method signature includes code, message, and optional details")

def test_error_codes_documented():
    """Test that error codes are documented in docstring."""
    method = getattr(VaultConsumer, '_send_error_and_close')
    docstring = method.__doc__ or ""

    required_codes = [
        'AUTH_FAILED',
        'PERMISSION_DENIED',
        'RATE_LIMIT_EXCEEDED',
        'VAULT_NOT_FOUND',
        'INTERNAL_ERROR'
    ]

    for code in required_codes:
        assert code in docstring, f"Error code '{code}' not documented in docstring"

    print(f"[OK] All required error codes documented: {', '.join(required_codes)}")

def test_method_implementation():
    """Test that method implementation includes required elements."""
    import inspect
    source = inspect.getsource(VaultConsumer._send_error_and_close)

    # Check for metadata timestamp
    assert 'metadata' in source, "Missing metadata in error payload"
    assert 'timestamp' in source, "Missing timestamp in metadata"
    assert 'datetime.now(timezone.utc)' in source, "Timestamp not using timezone-aware datetime"

    # Check for details field
    assert 'details' in source, "Missing details field in error payload"

    # Check for 2 second delay
    assert 'asyncio.sleep(2)' in source or 'await asyncio.sleep(2)' in source, "Missing 2 second delay before close"

    # Check for close with code 1008
    assert 'close(code=1008)' in source, "Connection close should use code 1008"

    # Check for logging
    assert 'logger.' in source, "Missing logging statement"

    print("[OK] Method implementation includes metadata, timestamp, details, 2s delay, code 1008, and logging")

def test_import_statements():
    """Test that required imports are present."""
    import apps.vaults.consumers as consumers_module
    source = inspect.getsource(consumers_module)

    assert 'import asyncio' in source or 'from asyncio' in source, "Missing asyncio import"
    assert 'from datetime import' in source and 'datetime' in source, "Missing datetime import"
    assert 'timezone' in source, "Missing timezone import"

    print("[OK] Required imports present: asyncio, datetime, timezone")

if __name__ == '__main__':
    print("Testing US-022: Error message format and close handling")
    print("=" * 60)

    test_send_error_method_exists()
    test_send_error_signature()
    test_error_codes_documented()
    test_import_statements()
    test_method_implementation()

    print("=" * 60)
    print("All tests passed!")
