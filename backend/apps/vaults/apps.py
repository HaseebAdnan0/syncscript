from django.apps import AppConfig


class VaultsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vaults'

    def ready(self):
        import apps.vaults.signals  # noqa: F401
