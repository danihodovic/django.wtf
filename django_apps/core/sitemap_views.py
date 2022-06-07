from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.urls import reverse

from .models import Category, Repository


class StaticSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return [
            "core:index",
            "core:top-profiles",
            "core:trending-profiles",
            "core:top-repositories",
            "core:trending-repositories",
            "core:social-media-news",
        ]

    def location(self, item):
        return reverse(item)


category_sitemap = GenericSitemap(
    dict(queryset=Category.objects.all(), changefreq="daily")
)

repository_sitemap = GenericSitemap(
    dict(queryset=Repository.valid.all(), changefreq="daily")
)


sitemaps = dict(
    static=StaticSitemap,
    categories=category_sitemap,
)
