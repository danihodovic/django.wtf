import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("django_apps")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    "index-repositories": {
        "task": "django_apps.core.tasks.index_repositories",
        "schedule": crontab(minute=0, hour=0),
    },
    "index-contributors": {
        "task": "django_apps.core.tasks.index_contributors",
        "schedule": crontab(minute=0, hour=1),
    },
    "categorize-repositories": {
        "task": "django_apps.core.tasks.categorize_repositories",
        "schedule": crontab(minute=0, hour=1),
    },
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
