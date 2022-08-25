from django.urls.base import reverse

from django_apps.core.factories import RepositoryFactory


class EmptyRepositoryFactory(RepositoryFactory):
    full_name = "nonmatch"
    description = "nonmatch"
    readme_html = "nonmatch"
    topics = ["nonmatch"]


def test_search_by_description(user_client):
    repo = RepositoryFactory(description="django")
    EmptyRepositoryFactory()
    res = user_client.get(reverse("watson:search"), dict(q="django"))
    assert res.status_code == 200
    search_results = res.context["search_results"]
    assert search_results.get().object == repo


def test_search_by_readme():
    res = reverse("watson:search")
    assert res.status_code == 200


def test_search_by_topics():
    res = reverse("watson:search")
    assert res.status_code == 200


def test_search_by_full_name():
    res = reverse("watson:search")
    assert res.status_code == 200
