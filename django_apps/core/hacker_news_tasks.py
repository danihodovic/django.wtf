import logging
from datetime import datetime

import pytz
import superrequests
from celery import current_app as app

from .models import SocialNews, SocialNewsType
from .utils import log_action


@app.task
def index_hn_submissions():
    # https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty
    client = superrequests.Session()
    res = client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    for item_id in res.json():
        submission_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        logging.info(f"Requesting: {submission_url}")
        res = client.get(submission_url)
        data = res.json()
        title = data["title"]
        if "django" in title.lower():
            logging.debug(f"Found HN submission that matches Django in {title=}")
            obj, created = SocialNews.objects.update_or_create(
                url=f"https://news.ycombinator.com/item?id={item_id}",
                defaults=dict(
                    type=SocialNewsType.HACKER_NEWS,
                    title=data["title"],
                    upvotes=data["score"],
                    created_at=datetime.fromtimestamp(data["time"], tz=pytz.utc),
                ),
            )
            log_action(obj, created)
