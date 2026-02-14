from django.apps import AppConfig


class CitationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.citations'

    def ready(self):
        """Import signals when app is ready."""
        import apps.citations.signals  # noqa: F401
