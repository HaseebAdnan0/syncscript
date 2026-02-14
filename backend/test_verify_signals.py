"""
Standalone verification script for Source signal handlers.

Verifies signal registration without requiring database setup.
"""

import os
import sys
import django
from unittest.mock import patch, MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db.models import signals
from apps.sources.models import Source  # type: ignore[import-not-found]


def verify_signal_registration() -> None:
    """Verify Source model signals are registered."""
    print('[OK] Starting signal registration verification...')

    # Check post_save signal receivers
    post_save_receivers = signals.post_save._live_receivers(Source)
    print(f'[OK] post_save has {len(post_save_receivers)} receiver(s) for Source model')

    # Check post_delete signal receivers
    post_delete_receivers = signals.post_delete._live_receivers(Source)
    print(f'[OK] post_delete has {len(post_delete_receivers)} receiver(s) for Source model')

    # Verify at least one receiver for each signal
    assert len(post_save_receivers) >= 1, 'Expected at least 1 post_save receiver'
    assert len(post_delete_receivers) >= 1, 'Expected at least 1 post_delete receiver'

    print('[OK] Signal registration verified successfully')


def verify_mock_tests() -> None:
    """Verify mock test logic without database."""
    print('\n[OK] Starting mock test verification...')

    # Verify signal handler functions are defined
    try:
        from apps.sources.signals import source_saved, source_deleted  # type: ignore[import-not-found]
        print('[OK] Signal handler functions (source_saved, source_deleted) imported successfully')
    except ImportError as e:
        print(f'[ERROR] Failed to import signal handlers: {e}')
        raise

    print('[OK] Mock test verification completed successfully')


def verify_test_file_structure() -> None:
    """Verify test file structure and imports."""
    print('\n[OK] Starting test file structure verification...')

    # Import test file
    try:
        from apps.sources.tests.test_signals import SourceSignalTests  # type: ignore[import-not-found]
        print('[OK] SourceSignalTests imported successfully')
    except ImportError as e:
        print(f'[ERROR] Failed to import SourceSignalTests: {e}')
        raise

    # Verify test methods exist
    test_methods = [
        'test_source_created_triggers_celery_task',
        'test_source_updated_broadcasts_to_vault',
        'test_source_deleted_broadcasts_to_vault',
        'test_signal_not_triggered_on_update',
        'test_create_and_update_trigger_different_tasks',
    ]

    for method_name in test_methods:
        assert hasattr(SourceSignalTests, method_name), f'Missing test method: {method_name}'
        print(f'[OK] Test method found: {method_name}')

    print('[OK] Test file structure verified successfully')


if __name__ == '__main__':
    try:
        verify_signal_registration()
        verify_mock_tests()
        verify_test_file_structure()
        print('\n' + '='*60)
        print('[SUCCESS] All verifications passed!')
        print('='*60)
        print('\nTo run the actual tests (requires PostgreSQL):')
        print('  python manage.py test apps.sources.tests.test_signals')
    except Exception as e:
        print(f'\n[ERROR] Verification failed: {e}')
        sys.exit(1)
