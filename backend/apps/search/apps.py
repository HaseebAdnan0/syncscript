from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures signal handlers are connected.
        """
        import apps.search.signals  # noqa: F401
