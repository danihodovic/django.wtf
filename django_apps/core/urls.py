from django.urls import path

from django_apps.core.views import CategoryView, ContributorsView, IndexView

app_name = "core"
urlpatterns = [
    path("", view=IndexView.as_view(), name="index"),
    path("category/<slug:name>/", view=CategoryView.as_view(), name="category-detail"),
    path("profiles/top/", view=ContributorsView.as_view(), name="profiles-top"),
]
