from django.apps import AppConfig


class AnnotationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.annotations'

    def ready(self) -> None:
        """Import signals when app is ready."""
        import apps.annotations.signals  # noqa: F401
