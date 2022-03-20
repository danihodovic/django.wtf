from django.views.generic.base import TemplateView

from .models import Repository


class IndexView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        repositories = Repository.objects.all().order_by("-stars")
        context = super().get_context_data(**kwargs)
        context["repositories"] = repositories
        return context
