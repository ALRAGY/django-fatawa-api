from django.apps import AppConfig

class SharedInboxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared_inbox'
    verbose_name = 'الصندوق الموحد'

    def ready(self):
        from .adapters.base import PlatformRegistry
        PlatformRegistry.load_all_adapters()
