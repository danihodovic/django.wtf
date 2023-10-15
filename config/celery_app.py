import os
from pathlib import Path

from celery import Celery, bootsteps
from celery.schedules import crontab
from celery.signals import worker_ready, worker_shutdown

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("django_wtf")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


HEARTBEAT_FILE = Path("/tmp/worker_heartbeat")
READINESS_FILE = Path("/tmp/worker_ready")


class LivenessProbe(bootsteps.StartStopStep):
    requires = {"celery.worker.components:Timer"}

    def __init__(
        self, worker, **kwargs
    ):  # pylint: disable=unused-argument,super-init-not-called
        self.requests = []
        self.tref = None

    def start(self, worker):  # pylint: disable=arguments-renamed
        self.tref = worker.timer.call_repeatedly(
            1.0,
            self.update_heartbeat_file,
            (worker,),
            priority=10,
        )

    def stop(self, worker):  # pylint: disable=unused-argument,arguments-renamed
        HEARTBEAT_FILE.unlink(missing_ok=True)

    def update_heartbeat_file(
        self, worker
    ):  # pylint: disable=unused-argument,arguments-renamed
        HEARTBEAT_FILE.touch()


@worker_ready.connect  # type: ignore
def worker_ready(**_):
    READINESS_FILE.touch()


@worker_shutdown.connect  # type: ignore
def worker_shutdown(**_):
    READINESS_FILE.unlink(missing_ok=True)


app.steps["worker"].add(LivenessProbe)

app.conf.beat_schedule = {
    "index-repositories-by-topic": {
        "task": "django_wtf.core.github_tasks.index_repositories_by_topic",
        "schedule": crontab(minute=0, hour=0),
    },
    "index-repositories-by-keyword": {
        "task": "django_wtf.core.github_tasks.index_repositories_by_keyword",
        "schedule": crontab(minute=5, hour=1),
    },
    "index-contributors": {
        "task": "django_wtf.core.github_tasks.index_contributors",
        "schedule": crontab(minute=10, hour=2),
    },
    "index-profile-followers": {
        "task": "django_wtf.core.github_tasks.index_followers",
        "schedule": crontab(minute=20, hour=3),
    },
    "index-readme": {
        "task": "django_wtf.core.github_tasks.index_repositories_readme",
        "schedule": crontab(minute=20, hour=8, day_of_week=5),
    },
    "categorize-repositories": {
        "task": "django_wtf.core.github_tasks.categorize_repositories",
        "schedule": crontab(minute=30, hour=4, day_of_week=0),
    },
    "social.index-reddit": {
        "task": "django_wtf.core.reddit_tasks.index_top_weekly_submissions",
        "schedule": crontab(minute=45, hour=4),
    },
    "social.index-hacker-news": {
        "task": "django_wtf.core.hacker_news_tasks.index_hn_submissions",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "index-pypi": {
        "task": "django_wtf.core.pypi_tasks.index_pypi_projects",
        "schedule": crontab(minute=0, hour=5, day_of_week=0),
    },
    "rebuild-search-index": {
        "task": "django_wtf.core.tasks.rebuild_search_index",
        "schedule": crontab(minute=0, hour="*/3"),
    },
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
