from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView

from django_wtf.core.models import Repository


class RepoDetailView(DetailView):
    def get_object(self, queryset=None):
        return get_object_or_404(Repository, full_name=self.kwargs.get("full_name"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        stars_since_1m = obj.stars_since(td=timedelta(days=30))
        context["stars_increase_monthly_percent"] = stars_since_1m / obj.stars * 1.0
        return context


repo_detail_view = RepoDetailView.as_view()
