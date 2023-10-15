from datetime import date, timedelta

import pytest

from .factories import RepositoryFactory, RepositoryStarsFactory

pytestmark = pytest.mark.django_db


def test_stars_since():
    repo = RepositoryFactory(stars=15)
    RepositoryStarsFactory(repository=repo, created_at=date(2021, 1, 1), stars=10)
    delta = repo.stars_since(timedelta(days=6), date=date(2021, 1, 7))
    assert delta == 5
