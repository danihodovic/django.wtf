from base64 import b64decode
from datetime import date

import markdown
import pypandoc
from constance import config
from django.db.models import Exists, OuterRef
from django.db.utils import DataError
from django.utils.http import urlencode
from django_o11y.logging.utils import get_logger
from requests.models import HTTPError
from urllib3.util.retry import Retry

from config import celery_app as app
from django_wtf.core.batching import dispatch_in_batches, run_batch
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
from django_wtf.core.rate_limit import ThrottledSession
from django_wtf.core.task_metrics import observe_external_api, record_indexing_event

from .utils import log_action

logger = get_logger()


@app.task(soft_time_limit=30 * 60)
def index_repositories_by_topic():
    index_repositories(search_repos_by_topic_url())


@app.task(soft_time_limit=30 * 60)
def index_repositories_by_keyword():
    index_repositories(search_repos_by_keyword_url())


def index_repositories(url):
    logger.info("github_repositories_page_requested", url=url)
    http = http_client("search")
    with observe_external_api("github", "search_repositories"):
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
    with observe_external_api("github", "repository_details"):
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
        logger.exception(
            "github_repository_upsert_data_error", repository_data=repository_data
        )
        record_indexing_event("github_repository", "data_error")


CORE_BATCH_SIZE = 50
# Code search allows far fewer requests, so keep batches small enough to finish
# within their time limit while waiting on the shared budget.
CODE_SEARCH_BATCH_SIZE = 5
FOLLOWERS_MIN_STARS = 70


@app.task(soft_time_limit=30 * 60)
def index_repositories_readme():
    dispatch_in_batches(
        index_repositories_readme_batch,
        Repository.valid.order_by("id").values_list("full_name", flat=True).iterator(),
        CORE_BATCH_SIZE,
        "github_readme",
    )


@app.task(ignore_result=True, soft_time_limit=45 * 60, time_limit=50 * 60)
def index_repositories_readme_batch(repo_full_names, pipeline):
    http = http_client()
    run_batch(
        lambda full_name: _index_repository_readme(http, full_name),
        repo_full_names,
        pipeline,
    )


@app.task()
def index_repository_readme(repo_full_name):
    _index_repository_readme(http_client(), repo_full_name)


def _index_repository_readme(http, repo_full_name):
    try:
        # Use the API since it retrieves the default branch
        with observe_external_api("github", "repository_readme_markdown"):
            res = http.get(
                f"https://api.github.com/repos/{repo_full_name}/contents/README.md"
            )
        markdown_text = b64decode(res.json()["content"]).decode("utf-8")
    except HTTPError as ex:
        if ex.response.status_code == 404:
            logger.info("github_readme_markdown_missing", repository=repo_full_name)
            logger.info(
                "github_readme_restructuredtext_attempt", repository=repo_full_name
            )
            record_indexing_event("github_readme", "missing_markdown")

            try:
                with observe_external_api(
                    "github", "repository_readme_restructuredtext"
                ):
                    res = http.get(
                        f"https://api.github.com/repos/{repo_full_name}/contents/README.rst"
                    )
                rst_text = b64decode(res.json()["content"]).decode("utf-8")
                markdown_text = pypandoc.convert_text(rst_text, "md", format="rst")
            except HTTPError as rst_ex:
                if ex.response.status_code == 404:
                    logger.info(
                        "github_readme_restructuredtext_missing",
                        repository=repo_full_name,
                    )
                    record_indexing_event("github_readme", "missing_restructuredtext")
                    return
                raise rst_ex
        else:
            raise ex

    repo = Repository.objects.get(full_name=repo_full_name)
    repo.readme_html = markdown.markdown(
        markdown_text, extensions=["extra", "codehilite"]
    )
    repo.save()


@app.task(soft_time_limit=30 * 60)
def index_contributors():
    dispatch_in_batches(
        index_contributors_batch,
        Repository.valid.order_by("id").values_list("id", flat=True).iterator(),
        CORE_BATCH_SIZE,
        "github_contributors",
    )


@app.task(ignore_result=True, soft_time_limit=45 * 60, time_limit=50 * 60)
def index_contributors_batch(repo_ids, pipeline):
    http = http_client()
    run_batch(
        lambda repo_id: _index_repo_contributors(http, repo_id), repo_ids, pipeline
    )


@app.task()
def index_repo_contributors(repo_id):
    _index_repo_contributors(http_client(), repo_id)


def _index_repo_contributors(http, repo_id):
    repo = Repository.objects.get(id=repo_id)
    url = f"https://api.github.com/repos/{repo.full_name}/contributors"
    with observe_external_api("github", "repository_contributors"):
        res = http.get(url)
    logger.info("github_contributors_index_started", repository=repo.full_name)
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
    # Profiles with a top contribution to a low-star repository are skipped, so
    # filter them out here rather than enqueueing work that exits immediately.
    low_star_contributions = Contributor.objects.filter(
        profile=OuterRef("pk"),
        contributions__gte=20,
        repository__stars__lt=FOLLOWERS_MIN_STARS,
    )
    profiles = Profile.contributes_to_valid_repos.all()
    record_indexing_event(
        "github_followers",
        "skipped_low_stars",
        profiles.filter(Exists(low_star_contributions)).count(),
    )
    dispatch_in_batches(
        index_followers_batch,
        profiles.exclude(Exists(low_star_contributions))
        .order_by("login")
        .values_list("login", flat=True)
        .iterator(),
        CORE_BATCH_SIZE,
        "github_followers",
    )


@app.task(ignore_result=True, soft_time_limit=45 * 60, time_limit=50 * 60)
def index_followers_batch(user_logins, pipeline):
    http = http_client()
    run_batch(
        lambda profile: _index_profile_followers(http, profile),
        Profile.objects.filter(login__in=user_logins),
        pipeline,
    )


@app.task()
def index_user_followers(user_login):
    _index_profile_followers(http_client(), Profile.objects.get(login=user_login))


def _index_profile_followers(http, profile):
    data = paginate(
        http,
        f"https://api.github.com/users/{profile.login}/followers?per_page=100",
    )
    followers = len(data)
    profile.followers = followers
    profile.save(update_fields=["followers", "modified"])
    profile_followers, created = ProfileFollowers.objects.update_or_create(
        profile=profile,
        created_at=date.today(),
        defaults={"followers": followers},
    )
    log_action(profile_followers, created)


# TODO: Use a generator
def paginate(http, url):
    data = []
    res = http.get(url)
    while True:
        data.extend(res.json())
        if "next" not in res.links:
            break
        res = http.get(res.links["next"]["url"])
    return data


@app.task(soft_time_limit=30 * 60)
def categorize_repositories():
    dispatch_in_batches(
        categorize_repositories_batch,
        Repository.objects.order_by("id")
        .values_list("full_name", flat=True)
        .iterator(),
        CODE_SEARCH_BATCH_SIZE,
        "github_repository_categorization",
    )


@app.task(ignore_result=True, soft_time_limit=25 * 60, time_limit=30 * 60)
def categorize_repositories_batch(repo_full_names, pipeline):
    http = http_client("code_search")
    run_batch(
        lambda full_name: _categorize_repository(http, full_name),
        repo_full_names,
        pipeline,
    )


@app.task()
def categorize_repository(repo_full_name):
    _categorize_repository(http_client("code_search"), repo_full_name)


def _categorize_repository(http, repo_full_name):
    repo = Repository.objects.get(full_name=repo_full_name)
    logger.info("github_repository_categorization_started", repository=repo.full_name)
    appconfig_files = find_appconfig_files(http, repo.full_name)
    pypi_project = PypiProject.objects.filter(repository=repo)
    # Has AppConfig means a Django app is configured somewhere
    if pypi_project and len(appconfig_files) > 0:
        repo_type = RepositoryType.APP
    elif len(appconfig_files) > 0:
        repo_type = RepositoryType.PROJECT
    else:
        repo_type = None
    logger.info(
        "github_repository_categorized",
        repository=repo.full_name,
        repository_type=repo_type,
    )
    if repo_type is None:
        record_indexing_event("github_repository_categorization", "uncategorized")
    else:
        record_indexing_event("github_repository_categorization", repo_type.lower())
    repo.type = repo_type
    repo.save()


def find_appconfig_files(http, repo_full_name):
    params = urlencode(
        {"q": f"repo:{repo_full_name} AppConfig in:file AppConfig language:python"}
    )
    with observe_external_api("github", "search_code_appconfig"):
        res = http.get("https://api.github.com/search/code", params=params)
    data = res.json()
    return [item for item in data["items"] if not item["path"].startswith("test")]


# Half of each GitHub quota, as requests per minute; the constance keys let us
# tune them without a deploy.
GITHUB_RATE_LIMITS = {
    "core": "GITHUB_CORE_REQUESTS_PER_MINUTE",
    "search": "GITHUB_SEARCH_REQUESTS_PER_MINUTE",
    "code_search": "GITHUB_CODE_SEARCH_REQUESTS_PER_MINUTE",
}


def http_client(bucket="core"):
    # Github rate limits with 403. Requests are throttled up front, so these
    # retries only cover the odd secondary rate limit or server error.
    retry_strategy = Retry(
        connect=3,
        read=3,
        total=5,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=30,
    )
    s = ThrottledSession(
        f"github:{bucket}",
        getattr(config, GITHUB_RATE_LIMITS[bucket]),
        retry_strategy=retry_strategy,
    )
    s.auth = ("danihodovic", config.GITHUB_TOKEN)
    return s
