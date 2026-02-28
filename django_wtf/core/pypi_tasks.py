from dateutil import parser
from django_o11y.logging.utils import get_logger
from requests.exceptions import HTTPError
from superrequests import Session

from config import celery_app as app
from django_wtf.core.models import PypiProject, PypiRelease, Repository
from django_wtf.core.task_metrics import observe_external_api, record_indexing_event

from .utils import log_action

http = Session()
logger = get_logger()


@app.task(soft_time_limit=30 * 60)
def index_pypi_projects():
    for repo in Repository.objects.all():
        index_pypi_project.delay(repo.full_name)


@app.task
def index_pypi_project(repo_full_name):
    repo = Repository.objects.get(full_name=repo_full_name)
    logger.info("pypi_project_index_started", repository=repo.full_name)
    try:
        with observe_external_api("pypi", "project_metadata"):
            res = http.get(f"https://pypi.org/pypi/{repo.name}/json")
    except HTTPError as ex:
        if ex.response.status_code == 404:
            logger.info("pypi_project_not_found", repository=repo.full_name)
            record_indexing_event("pypi_project", "not_found")
            return
        record_indexing_event("pypi_project", "error")
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
            logger.info(
                "pypi_release_data_missing",
                repository=repo.full_name,
                version=version,
            )
            record_indexing_event("pypi_release", "missing_data")
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
