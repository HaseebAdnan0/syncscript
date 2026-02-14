"""
Celery configuration for SyncScript.

This module initializes the Celery application for background task processing.
"""
from __future__ import absolute_import, unicode_literals

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('syncscript')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-orphaned-files-daily': {
        'task': 'apps.sources.tasks.cleanup_orphaned_files',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3:00 AM
    },
    'cleanup-orphaned-multipart-uploads-daily': {
        'task': 'apps.sources.tasks.cleanup_orphaned_multipart_uploads',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4:00 AM
    },
    'cleanup-deleted-pdfs-daily': {
        'task': 'apps.sources.tasks.cleanup_deleted_pdfs',
        'schedule': crontab(hour=5, minute=0),  # Daily at 5:00 AM
    },
    'cleanup-stale-websocket-connections': {
        'task': 'apps.vaults.tasks.cleanup_stale_connections',
        'schedule': 60.0,  # Every 60 seconds
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f'Request: {self.request!r}')
