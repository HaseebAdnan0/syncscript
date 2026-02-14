from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai'
    label = 'ai'

    def ready(self):
        """Import signal handlers when Django starts."""
        import apps.ai.signals  # noqa: F401
