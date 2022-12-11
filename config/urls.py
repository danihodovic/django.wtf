from typing import Any, List

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views import defaults as default_views
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns: List[Any] = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("django_apps.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Health checks
    path("health/", include("health_check.urls")),
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    re_path("", include("django_apps.core.urls")),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    re_path(r"^blog/", include(wagtail_urls)),
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)  # type: ignore


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
