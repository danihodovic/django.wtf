from django.views.generic import ListView
from meta.views import MetadataMixin

from django_wtf.core.models import Repository


class TopRepositoriesView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Top Django projects"
    description = "Most popular Django projects"
    template_name = "core/top_repositories.html"

    def get_queryset(self):
        return Repository.valid.order_by("-stars")
