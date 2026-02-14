from django.apps import AppConfig


class AnnotationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.annotations'

    def ready(self):
        # Import signals to register them
        import apps.annotations.signals  # type: ignore[import-not-found]  # noqa: F401
