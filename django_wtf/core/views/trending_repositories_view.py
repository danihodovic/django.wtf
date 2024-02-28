from constance import config
from django.views.generic import ListView
from meta.views import MetadataMixin

from django_wtf.core.queries import trending_repositories


class TrendingRepositoriesView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Trending Django projects"
    description = "Trending Django projects in the past week"
    template_name = "core/trending_repositories.html"

    def get_queryset(self):
        return trending_repositories()

    def get_meta_description(self, context=None):
        return f"Trending Django projects in the past {config.DAYS_SINCE_TRENDING} days"
