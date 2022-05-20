from datetime import datetime, timedelta

from cacheops import cached_as
from constance import config
from django.core.paginator import Paginator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from meta.views import MetadataMixin

from .models import (
    Category,
    Contributor,
    Profile,
    Repository,
    RepositoryStars,
    RepositoryType,
    SocialNews,
)


class IndexView(MetadataMixin, TemplateView):
    template_name = "core/index.html"
    title = "django.wtf: the unofficial Django package index"
    description = "django.wtf is a collection of Django packages, projects and tools."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = self.categories_ordered_by_total_repositories()
        context["trending_apps"] = trending_repositories()[0:5]
        context["trending_developers"] = trending_profiles()[0:5]
        one_week_ago = datetime.today().date() - timedelta(days=7)
        context["social_news"] = SocialNews.objects.filter(
            created_at__gt=one_week_ago
        ).order_by("-upvotes")[0:5]
        context["top_apps"] = Repository.valid.order_by("-stars")[0:5]
        return context

    # pylint: disable=no-self-use
    def categories_ordered_by_total_repositories(self):
        categories = []
        for c in Category.objects.all():
            count_matching_repositories = Repository.objects.filter(
                categories__in=[c]
            ).count()
            if count_matching_repositories:
                setattr(c, "total_repositories", count_matching_repositories)
                categories.append(c)
        return sorted(categories, key=lambda c: c.total_repositories, reverse=True)


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
        repos = Repository.valid.filter(categories__name=self.category_name).distinct()
        repos = repos.order_by("-stars")
        return repos

    @property
    def category_name(self):
        return self.kwargs.get("name")


class TrendingRepositoriesView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Trending Django projects"
    description = "Trending Django projects in the past week"
    template_name = "core/trending_repositories.html"

    def get_queryset(self):
        return trending_repositories()


class TopRepositoriesView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Top Django projects"
    description = "Most popular Django projects"
    template_name = "core/top_repositories.html"

    def get_queryset(self):
        return Repository.valid.order_by("-stars")


class TopProfilesView(MetadataMixin, ListView):
    template_name = "core/top_profiles.html"
    paginate_by = 25
    title = "Top contributors to Django projects"
    description = "Listing the top contributors to Django projects"

    def get_queryset(self):
        return most_followed_profiles()


class TrendingProfilesView(MetadataMixin, ListView):
    template_name = "core/trending_profiles.html"
    paginate_by = 25
    title = "Trending Django developers"
    description = "Listing the trending Django developers in the past two weeks"

    def get_queryset(self):
        return trending_profiles()


@cached_as(RepositoryStars, timeout=60 * 60 * 24)
def trending_repositories(**filters):
    trending = []
    for repo in Repository.valid.filter(stars__gte=20, **filters):
        stars_in_the_last_week = repo.stars_since(
            timedelta(days=config.DAYS_SINCE_TRENDING)
        )
        setattr(repo, "stars_lately", stars_in_the_last_week)
        trending.append(repo)

    return sorted(trending, key=lambda e: e.stars_lately, reverse=True)


@cached_as(Contributor, timeout=60 * 60 * 24)
def most_followed_profiles():
    repos = Repository.valid.filter(stars__gte=100)
    profile_ids = (
        Contributor.objects.filter(
            contributions__gt=20,
            repository__in=repos,
            profile__followers__gt=20,
        )
        .values_list("profile__id", flat=True)
        .order_by("profile__id")
        .distinct("profile__id")
    )
    return Profile.objects.filter(id__in=profile_ids).order_by("-followers")


@cached_as(Contributor, timeout=60 * 60 * 24)
def trending_profiles():
    # Contributed to a Django project
    # Sorted by most stars in the past two weeks
    trending = set()
    for profile in Profile.objects.filter(followers__gte=10):
        contributions = profile.top_contributions()
        for contribution in contributions:
            repo = contribution.repository
            if repo.type == RepositoryType.APP and repo.stars > 20:
                followers_lately = profile.followers_since(
                    timedelta(days=config.DAYS_SINCE_TRENDING)
                )
                setattr(profile, "followers_lately", followers_lately)
                trending.add(profile)
    return sorted(list(trending), key=lambda e: e.followers_lately, reverse=True)
