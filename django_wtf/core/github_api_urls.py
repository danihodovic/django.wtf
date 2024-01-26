from datetime import timedelta

from constance import config
from django.utils import timezone
from django.utils.http import urlencode

base_url = "https://api.github.com/search/repositories?"
common_params = {
    "sort": "stars",
    "order": "desc",
    "per_page": 100,
}


def search_repos_by_topic_url():
    q = f"topic:django stars:>20 pushed:>{date_since()} is:public"
    return base_url + urlencode({**common_params, **{"q": q}})  # type: ignore


def search_repos_by_keyword_url():
    q = f"django in:readme stars:>20 pushed:>{date_since()} is:public"
    return base_url + urlencode({**common_params, **{"q": q}})  # type: ignore


def date_since():
    days_ago_date = timezone.now() - timedelta(
        days=config.GITHUB_REPO_LAST_UPDATED_IN_DAYS
    )
    return days_ago_date.strftime("%Y-%m-%d")
