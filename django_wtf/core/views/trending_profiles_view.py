from constance import config
from django.views.generic import ListView
from meta.views import MetadataMixin

from django_wtf.core.queries import trending_profiles


class TrendingProfilesView(MetadataMixin, ListView):
    template_name = "core/trending_profiles.html"
    paginate_by = 25
    title = "Trending Django developers"
    description = "Listing the trending Django developers in the past two weeks"

    def get_queryset(self):
        return trending_profiles()

    def get_meta_description(self, context=None):
        return f"Trending Django projects in the past {config.DAYS_SINCE_TRENDING} days"
