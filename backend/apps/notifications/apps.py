"""
Django app configuration for notifications app.

Registers signal handlers for notification creation.
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for notifications app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

    def ready(self):
        """Import signal handlers when app is ready."""
        import apps.notifications.signals  # noqa: F401
