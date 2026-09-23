import pytest

from django_wtf.core.github_api_urls import search_repos_by_topic_url

from . import github_tasks
from .factories import ProfileFactory, ValidRepositoryFactory
from .github_tasks import index_contributors, index_repositories
from .models import Category, Contributor, ProfileFollowers, Repository

pytestmark = pytest.mark.django_db


@pytest.mark.override_config(GITHUB_TOKEN="very-secret")
def test_index_repositories(mocked_responses):
    mocked_responses.add(
        "GET",
        "https://api.github.com/search/repositories",
        json={
            "items": [
                {
                    "id": 22,
                    "name": "celery-exporter",
                    "full_name": "danihodovic/celery-exporter",
                    "forks": 2,
                    "watchers": 1,
                    "open_issues": 4,
                    "stargazers_count": 2,
                    "archived": False,
                    "topics": ["django"],
                    "description": "Hello",
                    "owner": {
                        "id": 11,
                        "login": "danihodovic",
                        "type": "user",
                        "avatar_url": "https://github.com/avatar",
                        "name": "celery-exporter",
                    },
                }
            ]
        },
    )
    mocked_responses.add(
        "GET",
        "https://api.github.com/repos/danihodovic/celery-exporter/contributors",
        json=[
            {
                "id": 11,
                "type": "user",
                "login": "danihodovic",
                "avatar_url": "https://github.com/avatar",
                "contributions": 3,
            },
            {
                "id": 12,
                "type": "user",
                "login": "adinhodovic",
                "avatar_url": "https://github.com/avatar",
                "contributions": 3,
            },
        ],
    )

    index_repositories(search_repos_by_topic_url())
    category = Category(name="monitoring", emoji="m")
    category.save()
    Repository.objects.get(full_name="danihodovic/celery-exporter").categories.add(
        category
    )
    index_contributors()

    repos = Repository.objects.all()
    assert len(repos) == 1
    repo = repos[0]
    assert repo.name == "celery-exporter"
    assert repo.stars == 2
    contributors = repo.contributors.all()
    assert len(contributors) == 2
    repository_stars = repo.repositorystars_set.first()
    assert repository_stars
    assert repository_stars.stars == 2
    assert (
        mocked_responses.calls[0].request.headers["Authorization"]
        == "Basic ZGFuaWhvZG92aWM6dmVyeS1zZWNyZXQ="
    )


@pytest.mark.override_config(GITHUB_TOKEN="very-secret")
def test_index_followers_batches_and_skips_low_star_contributors(
    mocked_responses, monkeypatch
):
    monkeypatch.setattr(github_tasks, "FOLLOWERS_BATCH_SIZE", 2)
    popular_repo = ValidRepositoryFactory(stars=500)
    small_repo = ValidRepositoryFactory(stars=10)
    indexed = [ProfileFactory(login=f"user-{i}") for i in range(3)]
    for profile in indexed:
        Contributor.objects.create(
            profile=profile, repository=popular_repo, contributions=50
        )
    skipped = ProfileFactory(login="skipped")
    Contributor.objects.create(profile=skipped, repository=small_repo, contributions=50)
    for profile in indexed:
        mocked_responses.add(
            "GET",
            f"https://api.github.com/users/{profile.login}/followers?per_page=100",
            json=[{"login": "a"}, {"login": "b"}],
        )

    sent = []
    monkeypatch.setattr(github_tasks.index_users_followers, "delay", sent.append)
    github_tasks.index_followers()

    assert sent == [["user-0", "user-1"], ["user-2"]]

    for batch in sent:
        github_tasks.index_users_followers(batch)
    for profile in indexed:
        profile.refresh_from_db()
        assert profile.followers == 2
        assert ProfileFollowers.objects.get(profile=profile).followers == 2
    skipped.refresh_from_db()
    assert skipped.followers is None
