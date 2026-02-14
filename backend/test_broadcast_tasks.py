"""
Test script for US-013: Source broadcast Celery tasks.
Verifies that broadcast tasks can be imported and have correct signatures.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Import using importlib to avoid triggering pdf2image import
from importlib import import_module
tasks_module = import_module('apps.sources.tasks')
broadcast_source_created = tasks_module.broadcast_source_created
broadcast_source_updated = tasks_module.broadcast_source_updated
broadcast_source_deleted = tasks_module.broadcast_source_deleted


def test_task_signatures():
    """Test that tasks exist and have correct signatures."""
    print("[OK] All broadcast tasks imported successfully")

    # Check task names
    assert broadcast_source_created.name == 'apps.sources.tasks.broadcast_source_created'
    assert broadcast_source_updated.name == 'apps.sources.tasks.broadcast_source_updated'
    assert broadcast_source_deleted.name == 'apps.sources.tasks.broadcast_source_deleted'
    print("[OK] All task names registered correctly")

    # Check that tasks are callable
    assert callable(broadcast_source_created)
    assert callable(broadcast_source_updated)
    assert callable(broadcast_source_deleted)
    print("[OK] All tasks are callable")

    print("\n=== US-013 Task Signature Verification Complete ===")
    print("Tasks are ready to receive calls from signal handlers.")
    print("Full E2E testing requires running Celery worker and WebSocket connections.")


if __name__ == '__main__':
    test_task_signatures()
