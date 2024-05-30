from django.templatetags.static import static
from django.views.generic.base import TemplateView
from meta.views import MetadataMixin

from django_wtf.core.models import Category, Repository, SocialNews
from django_wtf.core.queries import (
    one_week_ago,
    trending_profiles,
    trending_repositories,
)


def categories_ordered_by_total_repositories():
    categories = []
    for c in Category.objects.all():
        count_matching_repositories = Repository.objects.filter(
            categories__in=[c]
        ).count()
        if count_matching_repositories:
            setattr(c, "total_repositories", count_matching_repositories)
            categories.append(c)
    return sorted(categories, key=lambda c: c.total_repositories, reverse=True)


class IndexView(MetadataMixin, TemplateView):
    template_name = "core/index.html"
    title = "Django.WTF: The Django package index"
    description = (
        "Django.WTF lists popular Django projects, apps and tools. "
        "The latest and greatest news in the Django community."
    )
    keywords = [
        "django",
        "apps",
        "packages",
        "repositories",
        "python",
        "web",
        "framework",
        "apps",
        "tools",
        "news",
    ]
    use_schemaorg = True
    use_og = True
    use_twitter = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = categories_ordered_by_total_repositories()
        context["trending_apps"] = trending_repositories(days_since=14)[0:5]
        context["trending_developers"] = trending_profiles()[0:5]
        context["social_news"] = SocialNews.objects.filter(
            created_at__gt=one_week_ago
        ).order_by("-upvotes")[0:5]
        context["top_apps"] = Repository.valid.order_by("-stars")[0:5]
        return context

    def get_meta_image(self, context=None):
        return static("images/logo.png")
