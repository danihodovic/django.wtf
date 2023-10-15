from django.apps import AppConfig
from watson import search as watson

from .search_adapter import RepositorySearchAdapter


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_wtf.core"

    def ready(self):
        try:
            Repository = self.get_model("Repository")
            qs = Repository.valid.all()  # type: ignore
            watson.register(qs, RepositorySearchAdapter)

            # pylint: disable=unused-import,import-outside-toplevel
            import django_wtf.core.signals
        except ImportError:
            pass
