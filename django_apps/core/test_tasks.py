import pytest

from .models import Repository
from .tasks import index_repositories

pytestmark = pytest.mark.django_db


@pytest.mark.override_config(GITHUB_TOKEN="very-secret")
def test_index_repositories(mocked_responses):
    mocked_responses.add(
        "GET",
        "https://api.github.com/search/repositories",
        json=dict(
            items=[
                {
                    "id": 22,
                    "name": "celery-exporter",
                    "full_name": "danihodovic/celery-exporter",
                    "forks": 2,
                    "watchers": 1,
                    "open_issues": 4,
                    "stargazers_count": 2,
                    "owner": {
                        "id": 11,
                        "login": "danihodovic",
                        "type": "user",
                        "avatar_url": "https://github.com/avatar",
                        "name": "celery-exporter",
                    },
                }
            ]
        ),
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

    index_repositories()
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