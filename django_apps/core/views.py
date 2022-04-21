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
        context["trending_apps"] = trending_repositories(type=RepositoryType.APP)[0:10]
        context["categories"] = [
            ("auth", "⚿"),
            ("api", "⚘"),
            ("admin", "⚙"),
            ("email", "@"),
        ]
        context["trending_developers"] = [
            ("danihodovic", 44),
            ("adinhodovic", 30),
            ("denishodovic", 12),
            ("senadacomor", 9),
            ("janabuco", 7),
            ("bobgreat", 4),
            ("dingobingo", 4),
        ]
        context["apps"] = apps
        context["projects"] = projects
        return context


@cached_as(RepositoryStars, timeout=60 * 60 * 24)
def trending_repositories(**filters):
    trending = []
    for repo in Repository.objects.filter(stars__gte=20, **filters):
        try:
            stars_in_the_last_week = repo.stars_since(timedelta(days=12))
        except ObjectDoesNotExist:
            logging.debug(f"No previous stars found for {repo=}")
            continue
        setattr(repo, "stars_lately", stars_in_the_last_week)
        trending.append(repo)

    return sorted(trending, key=lambda e: e.stars_lately, reverse=True)
