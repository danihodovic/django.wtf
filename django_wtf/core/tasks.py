# pylint: disable=unused-import
from celery import current_app as app
from django.core.management import call_command

from .github_tasks import (
    index_contributors,
    index_followers,
    index_repositories_by_keyword,
    index_repositories_by_topic,
    index_repositories_readme,
    index_repository,
    index_repository_readme,
    index_user_followers,
)
from .hacker_news_tasks import index_hn_submissions
from .pypi_tasks import index_pypi_projects
from .reddit_tasks import index_top_weekly_submissions


@app.task(soft_time_limit=10 * 60)
def rebuild_search_index():
    call_command("buildwatson")
