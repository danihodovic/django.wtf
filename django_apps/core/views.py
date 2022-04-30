import logging
from datetime import timedelta

from cacheops import cached_as
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from meta.views import MetadataMixin

from .models import Category, Contributor, Repository, RepositoryStars, RepositoryType


class IndexView(MetadataMixin, TemplateView):
    template_name = "core/index.html"
    title = "django.wtf: the unofficial Django package index"
    description = "django.wtf is a collection of Django packages, projects and tools."

    def get_context_data(self, **kwargs):
        apps = Repository.objects.filter(type=RepositoryType.APP).order_by("-stars")
        projects = Repository.objects.filter(type=RepositoryType.PROJECT).order_by(
            "-stars"
        )
        context = super().get_context_data(**kwargs)
        context["trending_apps"] = trending_repositories(type=RepositoryType.APP)[0:10]
        context["categories"] = Category.objects.all()
        context["trending_developers"] = most_followed()[0:10]
        context["apps"] = apps
        context["projects"] = projects
        return context


class CategoryView(MetadataMixin, DetailView):
    model = Category

    def get_object(self, *args, **kwargs):
        return Category.objects.get(name=self.kwargs.get("name"))

    def get_context_data(self, *, _=None, **kwargs):  # pylint: disable=arguments-differ
        context = super().get_context_data()
        repos = self.matching_repositories()
        paginator = Paginator(repos, 25)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj
        context["category"] = self.get_object()
        return context

    def get_meta_title(self, context=None):
        return f"django.wtf: projects providing {self.category_name}"

    def get_meta_description(self, context=None):
        repos = self.matching_repositories()
        repo_names = ", ".join([r.full_name for r in repos[0:10]])
        return f"Common apps used for {self.category_name} are: {repo_names}"

    def matching_repositories(self):
        repos_by_category = Repository.objects.filter(
            categories__name=self.category_name
        )
        repos_by_topics = Repository.objects.filter(
            topics__contains=[self.category_name]
        )
        repos = repos_by_category.union(repos_by_topics)
        repos = repos.order_by("-stars")
        return repos

    @property
    def category_name(self):
        return self.kwargs.get("name")


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


@cached_as(Contributor, timeout=60 * 60 * 24)
def most_followed():
    repos = Repository.objects.filter(stars__gte=100, type__isnull=False)
    contributors = (
        Contributor.objects.filter(contributions__gte=10, repository__in=repos)
        .order_by("-contributions")
        .select_related("profile")
    )
    top_contributors = []
    for contributor in contributors:
        stars_contributions = contributor.repository.stars * contributor.contributions
        if (
            contributor.repository.type
            and contributor.contributions > 10
            and stars_contributions > 200
        ):
            top_contributors.append(contributor)
    profiles = {c.profile for c in contributors}
    return sorted(profiles, key=lambda e: e.followers or 0, reverse=True)
