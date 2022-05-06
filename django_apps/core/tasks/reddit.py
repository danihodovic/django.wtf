import logging
from datetime import datetime

import praw
import pytz
from celery import current_app as app
from constance import config

from ..models import SocialNews, SocialNewsType
from ..utils import log_action


def create_client():
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent="django.wtf crawler",
    )


@app.task(soft_time_limit=30 * 60)
def index_top_weekly_submissions():
    period = "week"
    logging.info(f"Indexing top Reddit posts by {period=}")
    subreddit = create_client().subreddit("django")
    for submission in subreddit.top(period):
        obj, created = SocialNews.objects.update_or_create(
            url=submission.url,
            defaults=dict(
                type=SocialNewsType.REDDIT,
                title=submission.title,
                upvotes=submission.ups,
                created_at=datetime.fromtimestamp(submission.created_utc, tz=pytz.utc),
            ),
        )
        log_action(obj, created)
