from django.urls import path

from django_apps.core.views import CategoryView, IndexView

app_name = "core"
urlpatterns = [
    path("", view=IndexView.as_view(), name="index"),
    path("category/<slug:name>/", view=CategoryView.as_view(), name="category-detail"),
]
