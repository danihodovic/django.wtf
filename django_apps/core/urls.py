from django.urls import path

from django_apps.core.views import IndexView

app_name = "core"
urlpatterns = [
    path("", view=IndexView.as_view(), name="index"),
]
