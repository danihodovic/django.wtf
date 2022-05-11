import logging
from datetime import date

import superrequests
from constance import config
from django.db.utils import DataError
from django.utils.http import urlencode

from config import celery_app as app
from django_apps.core.models import (
    Contributor,
    Profile,
    ProfileFollowers,
    Repository,
    RepositoryStars,
    RepositoryType,
)

from .utils import log_action


def http_client():
    s = superrequests.Session()
    s.auth = ("danihodovic", config.GITHUB_TOKEN)
    return s


@app.task(soft_time_limit=30 * 60)
def index_repositories(url):
    logging.info(f"GET {url=}")
    http = http_client()
    res = http.get(url)
    data = res.json()
    for repository_data in data["items"]:
        try:
            owner = repository_data["owner"]
            profile, _ = Profile.objects.update_or_create(
                github_id=owner["id"],
                defaults={
                    "login": owner["login"],
                    "type": owner["type"],
                    "avatar_url": owner["avatar_url"],
                },
            )

            repository, created = Repository.objects.update_or_create(
                github_id=repository_data["id"],
                defaults=dict(
                    owner=profile,
                    name=repository_data["name"],
                    full_name=repository_data["full_name"],
                    forks=repository_data["forks"],
                    watchers=repository_data["watchers"],
                    open_issues=repository_data["open_issues"],
                    stars=repository_data["stargazers_count"],
                    archived=repository_data["archived"],
                    topics=repository_data["topics"],
                    description=repository_data["description"],
                ),
            )
            log_action(repository, created)

            RepositoryStars.objects.update_or_create(
                repository=repository,
                created_at=date.today(),
                defaults=dict(stars=repository_data["stargazers_count"]),
            )
        except DataError:
            logging.exception(f"DataError for {repository=}")

    if "next" in res.links:
        next_url = res.links["next"]["url"]
        if next_url != url:
            index_repositories(url=next_url)


@app.task(soft_time_limit=60 * 60)
def index_contributors():
    for repo in Repository.objects.all():
        index_repo_contributors(repo.id)


@app.task()
def index_repo_contributors(repo_id):
    repo = Repository.objects.get(id=repo_id)
    url = f"https://api.github.com/repos/{repo.full_name}/contributors"
    http = http_client()
    res = http.get(url)
    logging.info(f"Indexing contributors for {repo=}")
    for entry in res.json():
        profile, _ = Profile.objects.update_or_create(
            github_id=entry["id"],
            defaults={
                "login": entry["login"],
                "type": entry["type"],
                "avatar_url": entry["avatar_url"],
            },
        )
        contributor, created = Contributor.objects.update_or_create(
            repository=repo,
            profile=profile,
            defaults=dict(contributions=entry["contributions"]),
        )
        log_action(contributor, created)


@app.task(soft_time_limit=30 * 60)
def index_followers():
    for profile in Profile.objects.all():
        index_user_followers(profile.login)


@app.task()
def index_user_followers(user_login):
    data = paginate(
        http_client(),
        f"https://api.github.com/users/{user_login}/followers?per_page=100",
    )
    followers = len(data)
    profile = Profile.objects.get(login=user_login)
    profile.followers = followers
    profile.save()
    profile_followers, created = ProfileFollowers.objects.update_or_create(
        profile=profile,
        created_at=date.today(),
        defaults=dict(followers=followers),
    )
    log_action(profile_followers, created)


@app.task(soft_time_limit=60 * 60)
def categorize_repositories():
    for repo in Repository.objects.all():
        categorize_repository.delay(repo.id)


# TODO: Use a generator
def paginate(http_client, url):  # pylint: disable=redefined-outer-name
    data = []
    res = http_client.get(url)
    while True:
        data.extend(res.json())
        if "next" not in res.links:
            break
        res = http_client.get(res.links["next"]["url"])
    return data


@app.task()
def categorize_repository(repository_id):
    repo = Repository.objects.get(id=repository_id)
    appconfig_files = find_appconfig_files(repo.full_name)
    contains_setup_files = has_setup_files(repo.full_name)
    # Has setup files means it's published to pip. Has AppConfig means
    # a Django app is configured somewhere
    if contains_setup_files and len(appconfig_files) > 0:
        repo_type = RepositoryType.APP
    elif len(appconfig_files) > 0:
        repo_type = RepositoryType.PROJECT
    else:
        repo_type = None
    logging.info(f"Categorizing {repo=} as {repo_type}")
    repo.type = repo_type
    repo.save()


def find_appconfig_files(repo_full_name):
    params = urlencode(
        dict(q=f"repo:{repo_full_name} AppConfig in:file AppConfig language:python")
    )
    http = http_client()
    res = http.get("https://api.github.com/search/code", params=params)
    data = res.json()
    return [item for item in data["items"] if not item["path"].startswith("test")]


def has_setup_files(repo_full_name):
    params = urlencode(dict(q=f"repo:{repo_full_name} setup.py in:path"))
    http = http_client()
    res = http.get("https://api.github.com/search/code", params=params)
    data = res.json()
    has_setup_py = False
    has_setup_cfg = False
    for entry in data["items"]:
        if entry["path"] == "setup.py":
            has_setup_py = True
        if entry["path"] == "setup.cfg":
            has_setup_cfg = True
        if has_setup_py and has_setup_cfg:
            return True
    return False