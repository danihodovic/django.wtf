from django.views.generic.base import TemplateView

from .models import Repository, RepositoryType


class IndexView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        apps = Repository.objects.filter(type=RepositoryType.APP).order_by("-stars")
        projects = Repository.objects.filter(type=RepositoryType.PROJECT).order_by(
            "-stars"
        )
        context = super().get_context_data(**kwargs)
        context["apps"] = apps
        context["projects"] = projects
        return context
