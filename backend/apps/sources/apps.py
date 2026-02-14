"""
Django app configuration for sources app.

Registers signal handlers for Source model changes.
"""
from django.apps import AppConfig


class SourcesConfig(AppConfig):
    """Configuration for sources app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sources'

    def ready(self):
        """Import signal handlers when app is ready."""
        import apps.sources.signals  # noqa: F401
