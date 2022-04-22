import logging
from datetime import timedelta

from cacheops import cached_as
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from .models import Category, Repository, RepositoryStars, RepositoryType


class IndexView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        apps = Repository.objects.filter(type=RepositoryType.APP).order_by("-stars")
        projects = Repository.objects.filter(type=RepositoryType.PROJECT).order_by(
            "-stars"
        )
        context = super().get_context_data(**kwargs)
        context["trending_apps"] = trending_repositories(type=RepositoryType.APP)[0:10]
        context["categories"] = Category.objects.all()
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


class CategoryView(DetailView):
    model = Category

    def get_object(self, *args, **kwargs):
        return Category.objects.get(name=self.kwargs.get("name"))

    def get_context_data(self, *, _=None, **kwargs):  # pylint: disable=arguments-differ
        context = super().get_context_data()
        category = self.kwargs.get("name")
        repos_by_category = Repository.objects.filter(categories__name=category)
        repos_by_topics = Repository.objects.filter(topics__contains=[category])
        repos = repos_by_category.union(repos_by_topics)
        repos = repos.order_by("-stars")
        paginator = Paginator(repos, 25)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["repositories"] = page_obj
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
