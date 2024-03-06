import logging
from base64 import b64decode
from datetime import date

import markdown
import superrequests
from constance import config
from django.db.utils import DataError
from django.utils.http import urlencode
from requests.models import HTTPError
from urllib3.util.retry import Retry

from config import celery_app as app
from django_wtf.core.github_api_urls import (
    search_repos_by_keyword_url,
    search_repos_by_topic_url,
)
from django_wtf.core.models import (
    Contributor,
    Profile,
    ProfileFollowers,
    PypiProject,
    Repository,
    RepositoryStars,
    RepositoryType,
)

from .utils import log_action


@app.task(soft_time_limit=30 * 60)
def index_repositories_by_topic():
    index_repositories(search_repos_by_topic_url())


@app.task(soft_time_limit=30 * 60)
def index_repositories_by_keyword():
    index_repositories(search_repos_by_keyword_url())


def index_repositories(url):
    logging.info(f"GET {url=}")
    http = http_client()
    res = http.get(url)
    data = res.json()
    for repository_data in data["items"]:
        _update_or_create_repo(repository_data)

    if "next" in res.links:
        next_url = res.links["next"]["url"]
        if next_url != url:
            index_repositories(url=next_url)


@app.task
def index_repository(full_name):
    http = http_client()
    res = http.get(f"https://api.github.com/repos/{full_name}")
    _update_or_create_repo(res.json())


def _update_or_create_repo(repository_data):
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
            defaults={
                "owner": profile,
                "name": repository_data["name"],
                "full_name": repository_data["full_name"],
                "forks": repository_data["forks"],
                "watchers": repository_data["watchers"],
                "open_issues": repository_data["open_issues"],
                "stars": repository_data["stargazers_count"],
                "archived": repository_data["archived"],
                "topics": repository_data["topics"],
                "description": repository_data["description"],
            },
        )
        log_action(repository, created)

        repository_stars, created = RepositoryStars.objects.update_or_create(
            repository=repository,
            created_at=date.today(),
            defaults={"stars": repository_data["stargazers_count"]},
        )
        log_action(repository_stars, created)
    except DataError:
        logging.exception(f"DataError for {repository_data=}")


@app.task()
def index_repositories_readme():
    for repo in Repository.valid.all():
        index_repository_readme.delay(repo.full_name)


@app.task()
def index_repository_readme(repo_full_name):
    http = http_client()
    try:
        # Use the API since it retrieves the default branch
        res = http.get(
            f"https://api.github.com/repos/{repo_full_name}/contents/README.md"
        )
    except HTTPError as ex:
        if ex.response.status_code == 404:
            logging.info(f"{repo_full_name} has no README.md file")
            return
        raise ex

    markdown_text = b64decode(res.json()["content"]).decode("utf-8")
    repo = Repository.objects.get(full_name=repo_full_name)
    repo.readme_html = markdown.markdown(markdown_text)
    repo.save()


@app.task(soft_time_limit=60 * 60)
def index_contributors():
    for repo in Repository.valid.all():
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
            defaults={"contributions": entry["contributions"]},
        )
        log_action(contributor, created)


@app.task(soft_time_limit=30 * 60)
def index_followers():
    for profile in Profile.contributes_to_valid_repos.all():
        index_user_followers.delay(profile.login)


@app.task()
def index_user_followers(user_login):
    profile = Profile.objects.get(login=user_login)

    for contribution in profile.top_contributions():
        min_stars = 70
        if min_stars > contribution.repository.stars:
            logging.info(
                f"Avoiding to retrieve ProfileFollowers for {profile=}. "
                "No repo they contribute to has more than {min_stars} stars"
            )
            return

    data = paginate(
        http_client(),
        f"https://api.github.com/users/{user_login}/followers?per_page=100",
    )
    followers = len(data)
    profile.followers = followers
    profile.save()
    profile_followers, created = ProfileFollowers.objects.update_or_create(
        profile=profile,
        created_at=date.today(),
        defaults={"followers": followers},
    )
    log_action(profile_followers, created)


@app.task(soft_time_limit=60 * 60)
def categorize_repositories():
    for repo in Repository.objects.all():
        categorize_repository.delay(repo.full_name)


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
def categorize_repository(repo_full_name):
    repo = Repository.objects.get(full_name=repo_full_name)
    logging.info(f"Categorizing {repo=}")
    appconfig_files = find_appconfig_files(repo.full_name)
    pypi_project = PypiProject.objects.filter(repository=repo)
    # Has AppConfig means a Django app is configured somewhere
    if pypi_project and len(appconfig_files) > 0:
        repo_type = RepositoryType.APP
    elif len(appconfig_files) > 0:
        repo_type = RepositoryType.PROJECT
    else:
        repo_type = None
    logging.info(f"Categorizing {repo=} as {repo_type}")
    repo.type = repo_type
    repo.save()


@app.task()
def download_markdown_html():
    import base64

    repo = "danihodovic/celery-exporter"
    token = ""

    http = http_client()
    headers = {"Authorization": f"Bearer {token}" "X-GitHub-Api-Version: 2022-11-28"}

    res = http.get(
        f"https://api.github.com/repos/{repo}/contents/README.md",
        headers=headers,
    )

    base64_content = res.json()["content"]
    content = base64.b64decode(base64_content).decode("utf-8")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    res = http.post(
        "https://api.github.com/markdown", headers=headers, json={"text": content}
    )
    return res


def find_appconfig_files(repo_full_name):
    params = urlencode(
        {"q": f"repo:{repo_full_name} AppConfig in:file AppConfig language:python"}
    )
    http = http_client()
    res = http.get("https://api.github.com/search/code", params=params)
    data = res.json()
    return [item for item in data["items"] if not item["path"].startswith("test")]


def http_client():
    # Github rate limits with 403
    retry_strategy = Retry(
        connect=3,
        read=3,
        total=300,
        status=300,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=60,
    )
    s = superrequests.Session(retry_strategy=retry_strategy)
    s.auth = ("danihodovic", config.GITHUB_TOKEN)
    return s
