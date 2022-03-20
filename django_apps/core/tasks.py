from datetime import date

import requests
from celery import current_app as app
from constance import config

from .models import Contributor, Profile, Repository, RepositoryStars


def http_client():
    s = requests.Session()
    s.auth = ("danihodovic", config.GITHUB_TOKEN)
    return s


@app.task()
def index_repositories():
    http = http_client()
    res = http.get(
        "https://api.github.com/search/repositories",
        params=dict(
            q="topic:django stars:>25 pushed:>2021-01-01 is:public",
            sort="stars",
            order="desc",
            per_page=100,
        ),
    )
    res.raise_for_status()
    data = res.json()
    for repository_data in data["items"]:
        owner = repository_data["owner"]
        profile, _ = Profile.objects.update_or_create(
            github_id=owner["id"],
            defaults={
                "login": owner["login"],
                "type": owner["type"],
                "avatar_url": owner["avatar_url"],
            },
        )
        repository, _ = Repository.objects.update_or_create(
            github_id=repository_data["id"],
            defaults=dict(
                owner=profile,
                name=repository_data["name"],
                full_name=repository_data["full_name"],
                forks=repository_data["forks"],
                watchers=repository_data["watchers"],
                open_issues=repository_data["open_issues"],
                stars=repository_data["stargazers_count"],
            ),
        )
        RepositoryStars.objects.update_or_create(
            repository=repository,
            created_at=date.today(),
            defaults=dict(stars=repository_data["stargazers_count"]),
        )
        index_contributors(repository.full_name)


@app.task()
def index_contributors(repository_full_name):
    http = http_client()
    url = f"https://api.github.com/repos/{repository_full_name}/contributors"
    res = http.get(url)
    res.raise_for_status()
    repository = Repository.objects.get(full_name=repository_full_name)
    for entry in res.json():
        profile, _ = Profile.objects.update_or_create(
            github_id=entry["id"],
            defaults={
                "login": entry["login"],
                "type": entry["type"],
                "avatar_url": entry["avatar_url"],
            },
        )
        _, _ = Contributor.objects.update_or_create(
            repository=repository,
            profile=profile,
            defaults=dict(contributions=entry["contributions"]),
        )
