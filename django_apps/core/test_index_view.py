import pytest
from django.urls import reverse_lazy

from .factories import RepositoryFactory
from .models import Category, RepositoryType

pytestmark = pytest.mark.django_db
url = reverse_lazy("core:index")


def test_index_lists_top_apps(client):
    RepositoryFactory(
        full_name="danihodovic/celery-exporter",
        stars=1,
        categories=[],
        type=RepositoryType.APP,
    )
    RepositoryFactory(
        full_name="getsentry/sentry",
        stars=100,
        categories=(
            Category(name="projects", emoji="p"),
            Category(name="monitoring", emoji="m"),
        ),
        type=RepositoryType.PROJECT,
    )
    res = client.get(url)
    assert res.status_code == 200
    top_apps = res.context["top_apps"]
    assert len(top_apps) == 2
    assert top_apps[0].full_name == "getsentry/sentry"
    assert top_apps[1].full_name == "danihodovic/celery-exporter"
