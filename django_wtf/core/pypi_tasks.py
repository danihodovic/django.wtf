from dateutil import parser
from django_o11y.logging.utils import get_logger
from requests.exceptions import HTTPError
from superrequests import Session

from config import celery_app as app
from django_wtf.core.models import PypiProject, PypiRelease, Repository
from django_wtf.core.task_metrics import (
    observe_external_api,
    record_indexing_event,
    record_value_truncation,
)

from .utils import log_action

http = Session()
logger = get_logger()


def _safe_metadata_value(field, value, max_length, *, nullable=False):
    if value is None:
        return None if nullable else ""
    value = str(value)
    if len(value) > max_length:
        record_value_truncation("pypi_project", field, max_length)
        return value[:max_length]
    return value


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
            "author": _safe_metadata_value("author", info.get("author"), 100),
            "author_email": _safe_metadata_value(
                "author_email", info.get("author_email"), 254
            ),
            "homepage": _safe_metadata_value("homepage", info.get("home_page"), 200),
            "summary": _safe_metadata_value("summary", info.get("summary"), 300),
            "version": _safe_metadata_value("version", info.get("version"), 12),
            "requires_python": _safe_metadata_value(
                "requires_python", info.get("requires_python"), 20, nullable=True
            ),
            "license": _safe_metadata_value("license", info.get("license"), 70),
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
