from django.apps import AppConfig
from watson import search as watson


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_apps.core"

    def ready(self):
        try:
            Repository = self.get_model("Repository")
            watson.register(Repository)
            # pylint: disable=unused-import,import-outside-toplevel
            import django_apps.core.signals
        except ImportError:
            pass
