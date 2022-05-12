from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_apps.core"

    def ready(self):
        try:
            # pylint: disable=unused-import,import-outside-toplevel
            import django_apps.core.signals
        except ImportError:
            pass
