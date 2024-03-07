from datetime import datetime, timedelta

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_trending_by_week(
    valid_repository_factory, repository_stars_factory, user_client
):
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    url = reverse("core:trending-repositories")
    more_popular = valid_repository_factory(stars=32)
    less_popular = valid_repository_factory(stars=40)
    repository_stars_factory(
        repository=more_popular, created_at=seven_days_ago, stars=2
    )
    repository_stars_factory(
        repository=less_popular, created_at=seven_days_ago, stars=10
    )

    res = user_client.get(url + "?trending=7")
    assert res.context["object_list"][0] == more_popular
    assert res.context["object_list"][1] == less_popular
    assert res.context["object_list"][0].stars_lately == 30
    assert res.context["object_list"][0].stars_quota == 0.9375
    assert res.context["object_list"][1].stars_lately == 30
    assert res.context["object_list"][1].stars_quota == 0.75
