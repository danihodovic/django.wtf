from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "django_wtf.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            # pylint: disable=unused-import,import-outside-toplevel
            import django_wtf.users.signals  # noqa F401
        except ImportError:
            pass
