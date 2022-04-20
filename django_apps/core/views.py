import logging
from datetime import timedelta

from cacheops import cached_as
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.base import TemplateView

from .models import Repository, RepositoryStars, RepositoryType


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


@cached_as(RepositoryStars, timeout=60 * 60 * 24)
def trending_repositories():
    trending = []
    for repo in Repository.objects.filter(stars__gte=20):
        try:
            stars_in_the_last_week = repo.stars_since(timedelta(days=12))
        except ObjectDoesNotExist:
            logging.debug(f"No previous stars found for {repo=}")
            continue
        trending.append((repo.full_name, stars_in_the_last_week))

    return sorted(trending, key=lambda e: e[1], reverse=True)
