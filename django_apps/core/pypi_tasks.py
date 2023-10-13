import logging

from dateutil import parser
from requests.exceptions import HTTPError
from superrequests import Session

from config import celery_app as app
from django_apps.core.models import PypiProject, PypiRelease, Repository

from .utils import log_action

http = Session()


@app.task(soft_time_limit=30 * 60)
def index_pypi_projects():
    for repo in Repository.objects.all():
        index_pypi_project.delay(repo.full_name)


@app.task
def index_pypi_project(repo_full_name):
    repo = Repository.objects.get(full_name=repo_full_name)
    logging.info(f"Indexing {repo=}")
    try:
        res = http.get(f"https://pypi.org/pypi/{repo.name}/json")
    except HTTPError as ex:
        if ex.response.status_code == 404:
            logging.info(f"404 - failed to index {repo=}")
            return
        raise ex
    data = res.json()
    info = data["info"]

    pypi_project, created = PypiProject.objects.update_or_create(
        repository=repo,
        defaults={
            "author": info["author"],
            "author_email": info["author_email"],
            "homepage": info["home_page"],
            "summary": info["summary"],
            "version": info["version"],
            "requires_python": info["requires_python"],
            "license": info["license"],
        },
    )
    log_action(pypi_project, created)

    for version, release_obj in data["releases"].items():
        if not release_obj:
            logging.info(f"No release data found for {repo=} {version=}")
            continue

        release_data = release_obj[0]
        pypi_release, created = PypiRelease.objects.update_or_create(
            project=pypi_project,
            version=version,
            defaults={
                "uploaded_at": parser.parse(release_data["upload_time_iso_8601"])
            },
        )
        log_action(pypi_release, created)
