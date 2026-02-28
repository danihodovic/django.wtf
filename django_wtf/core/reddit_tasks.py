from datetime import UTC, datetime

import praw
from celery import current_app as app
from constance import config
from django.db import DataError
from django_o11y.logging.utils import get_logger
from django_wtf.core.task_metrics import record_indexing_event

from .models import SocialNews, SocialNewsType
from .utils import log_action

logger = get_logger()


def create_client():
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent="django.wtf crawler",
    )


@app.task(soft_time_limit=30 * 60)
def index_top_weekly_submissions():
    period = "week"
    logger.info("reddit_index_started", period=period)
    subreddit = create_client().subreddit("django")
    for submission in subreddit.top(period):
        try:
            obj, created = SocialNews.objects.update_or_create(
                url=submission.url,
                defaults={
                    "type": SocialNewsType.REDDIT,
                    "title": submission.title,
                    "upvotes": submission.ups,
                    "created_at": datetime.fromtimestamp(
                        submission.created_utc, tz=UTC
                    ),
                },
            )
        except DataError as ex:
            permalink = submission.permalink
            logger.warning(
                "reddit_submission_index_failed",
                permalink=permalink,
                error_args=ex.args,
            )
            record_indexing_event("reddit_submission", "error")
            continue

        log_action(obj, created)
