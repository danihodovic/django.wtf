from django.contrib.sitemaps.views import sitemap
from django.urls import path

from django_wtf.core.search_view import SearchView
from django_wtf.core.views import (
    CategoryView,
    IndexView,
    SocialMediaNewsView,
    TopProfilesView,
    TopRepositoriesView,
    TrendingProfilesView,
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
    path(
        "social-media-news/",
        view=SocialMediaNewsView.as_view(),
        name="social-media-news",
    ),
    path("profiles/top/", view=TopProfilesView.as_view(), name="top-profiles"),
    path(
        "profiles/trending/",
        view=TrendingProfilesView.as_view(),
        name="trending-profiles",
    ),
    path("category/<slug:name>/", view=CategoryView.as_view(), name="category-detail"),
    path("search/", view=SearchView.as_view(), name="search"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]