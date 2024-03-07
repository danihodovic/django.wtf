from collections import OrderedDict

from constance import config
from django.views.generic import ListView
from meta.views import MetadataMixin

from django_wtf.core.queries import trending_repositories


class TrendingRepositoriesView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Trending Django projects"
    description = "Trending Django projects in the past week"
    template_name = "core/trending_repositories.html"
    periods = OrderedDict(
        [
            (7, "7 days"),
            (14, "14 days"),
            (30, "30 days"),
            (90, "3 months"),
            (365, "1 year"),
        ]
    )

    def get_queryset(self):
        trending = trending_repositories(self.get_period_value())
        return trending

    def get_period_value(self):
        period_q = self.request.GET.get("trending", 14)
        valid_value = period_q in [str(k) for k in self.periods.keys()]
        return int(period_q) if valid_value else 14

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["periods"] = self.periods.items()
        current_period_label = self.periods.get(self.get_period_value())
        context["current_period"] = self.get_period_value()
        context["current_period_label"] = current_period_label
        return context

    def get_meta_description(self, context=None):
        return f"Trending Django projects in the past {config.DAYS_SINCE_TRENDING} days"
