import json
import os

from celery import Celery
from celery.schedules import crontab

from django_apps.core.github_api_urls import (
    search_repos_by_keyword_url,
    search_repos_by_topic_url,
)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("django_apps")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    "index-repositories-by-topic": {
        "task": "django_apps.core.github_tasks.index_repositories",
        "schedule": crontab(minute=0, hour=0),
        "args": json.dumps([search_repos_by_topic_url]),
    },
    "index-repositories-by-keyword": {
        "task": "django_apps.core.github_tasks.index_repositories",
        "schedule": crontab(minute=5, hour=1),
        "args": json.dumps([search_repos_by_keyword_url]),
    },
    "index-contributors": {
        "task": "django_apps.core.github_tasks.index_contributors",
        "schedule": crontab(minute=10, hour=2),
    },
    "index-profile-followers": {
        "task": "django_apps.core.github_tasks.index_followers",
        "schedule": crontab(minute=20, hour=3),
    },
    "categorize-repositories": {
        "task": "django_apps.core.github_tasks.categorize_repositories",
        "schedule": crontab(minute=30, hour=4),
    },
    "social.index-reddit": {
        "task": "django_apps.core.reddit_tasks.index_top_weekly_submissions",
        "schedule": crontab(minute=45, hour=4),
    },
    "social.index-hacker-news": {
        "task": "django_apps.core.hacker_news_tasks.index_hn_submissions",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "index-pypi": {
        "task": "django_apps.core.pypi_tasks.index_pypi_projects",
        "schedule": crontab(minute=0, hour=5, day_of_week=0),
    },
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
