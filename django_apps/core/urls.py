from django.contrib.sitemaps.views import sitemap
from django.urls import path

from django_apps.core.views import (
    CategoryView,
    ContributorsView,
    IndexView,
    TopRepositoriesView,
    TrendingRepositoriesView,
)

from .sitemap_views import sitemaps

app_name = "core"
urlpatterns = [
    path("", view=IndexView.as_view(), name="index"),
    path(
        "trending/",
        view=TrendingRepositoriesView.as_view(),
        name="trending-repositories",
    ),
    path(
        "top/",
        view=TopRepositoriesView.as_view(),
        name="top-repositories",
    ),
    path("profiles/top/", view=ContributorsView.as_view(), name="top-profiles"),
    path("category/<slug:name>/", view=CategoryView.as_view(), name="category-detail"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]
