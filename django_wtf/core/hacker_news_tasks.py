from datetime import UTC, datetime

import superrequests
from celery import current_app as app
from django_o11y.logging.utils import get_logger
from django_wtf.core.task_metrics import observe_external_api, record_indexing_event

from .models import SocialNews, SocialNewsType
from .utils import log_action

logger = get_logger()


@app.task(soft_time_limit=30 * 60)
def index_hn_submissions():
    # https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty
    client = superrequests.Session()
    with observe_external_api("hacker_news", "list_newstories"):
        res = client.get("https://hacker-news.firebaseio.com/v0/newstories.json")
    for item_id in res.json():
        submission_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        logger.info("hacker_news_submission_requested", submission_url=submission_url)
        with observe_external_api("hacker_news", "fetch_item"):
            res = client.get(submission_url)
        data = res.json()
        title = data["title"]
        if "django" in title.lower():
            logger.debug("hacker_news_django_match_found", title=title)
            record_indexing_event("hacker_news_submission", "django_match")
            obj, created = SocialNews.objects.update_or_create(
                url=f"https://news.ycombinator.com/item?id={item_id}",
                defaults={
                    "type": SocialNewsType.HACKER_NEWS,
                    "title": data["title"],
                    "upvotes": data["score"],
                    "created_at": datetime.fromtimestamp(data["time"], tz=UTC),
                },
            )
            log_action(obj, created)
