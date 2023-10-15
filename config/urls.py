from typing import Any

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.urls import include, path
from django.views import defaults as default_views
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import Sitemap as wagtail_sitemap_view
from wagtail.documents import urls as wagtaildocs_urls

from django_wtf.core.sitemap_views import sitemaps as core_sitemaps

sitemaps = {**core_sitemaps, "blog": wagtail_sitemap_view}


urlpatterns: list[Any] = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("django_wtf.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Health checks
    path("health/", include("health_check.urls")),
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path(
        "sitemap.xml",
        sitemap_view,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("blog/", include(wagtail_urls)),
    path("", include("django_wtf.core.urls")),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
        urlpatterns = [
            path("__reload__/", include("django_browser_reload.urls")),
            *urlpatterns,
        ]
