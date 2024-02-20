from datetime import datetime, timedelta

from cacheops import cached_as
from constance import config
from constance.backends.database.models import Constance
from django.core.paginator import Paginator
from django.templatetags.static import static
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
    SocialNews,
)

one_week_ago = datetime.today().date() - timedelta(days=7)


class IndexView(MetadataMixin, TemplateView):
    template_name = "core/index.html"
    title = "Django.WTF: The Django package index"
    description = (
        "Django.WTF lists popular Django projects, apps and tools. "
        "The latest and greatest news in the Django community."
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = self.categories_ordered_by_total_repositories()
        context["trending_apps"] = trending_repositories()[0:5]
        context["trending_developers"] = trending_profiles()[0:5]
        context["social_news"] = SocialNews.objects.filter(
            created_at__gt=one_week_ago
        ).order_by("-upvotes")[0:5]
        context["top_apps"] = Repository.valid.order_by("-stars")[0:5]
        return context

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

    def get_meta_image(self, context=None):
        return static("images/logo.png")


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
        context["paginator"] = paginator
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

    def get_meta_description(self, context=None):
        return f"Trending Django projects in the past {config.DAYS_SINCE_TRENDING} days"


class TopRepositoriesView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Top Django projects"
    description = "Most popular Django projects"
    template_name = "core/top_repositories.html"

    def get_queryset(self):
        return Repository.valid.order_by("-stars")


class SocialMediaNewsView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Django News"
    description = "Django social media news"
    template_name = "core/social_media_news.html"

    def get_queryset(self):
        return SocialNews.objects.filter(created_at__gt=one_week_ago).order_by(
            "-upvotes"
        )


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

    def get_meta_description(self, context=None):
        return f"Trending Django projects in the past {config.DAYS_SINCE_TRENDING} days"


@cached_as(RepositoryStars, Constance, timeout=60 * 60 * 24)
def trending_repositories(**filters):
    trending = []
    for repo in Repository.valid.filter(stars__gte=20, **filters):
        stars_in_the_last_week = repo.stars_since(
            timedelta(days=config.DAYS_SINCE_TRENDING)
        )
        if stars_in_the_last_week > 0:
            setattr(repo, "stars_lately", stars_in_the_last_week)
            setattr(repo, "stars_quota", repo.stars_lately / repo.stars)  # type: ignore
            trending.append(repo)

    return sorted(trending, key=lambda e: e.stars_quota, reverse=True)


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
    return Profile.contributes_to_valid_repos.filter(id__in=profile_ids).order_by(
        "-followers"
    )


@cached_as(Contributor, Constance, timeout=60 * 60 * 24)
def trending_profiles():
    # Contributed to a Django project
    # Sorted by most stars in the past two weeks
    trending = set()
    profiles = Profile.contributes_to_valid_repos.filter(
        contributor__contributions__gte=20,
        contributor__repository__stars__gte=20,
        followers__gte=10,
    )
    for profile in profiles:
        followers_lately = profile.followers_since(
            timedelta(days=config.DAYS_SINCE_TRENDING)
        )
        if followers_lately > 0:
            setattr(profile, "followers_lately", followers_lately)
            trending.add(profile)
    return sorted(list(trending), key=lambda e: e.followers_lately, reverse=True)
