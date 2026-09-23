# pylint: disable=redefined-outer-name
from unittest.mock import Mock

import pytest

from . import rate_limit
from .rate_limit import ThrottledSession, throttle


@pytest.fixture
def sleep(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(rate_limit.time, "sleep", mock)
    return mock


@pytest.fixture
def clock(monkeypatch):
    now = [600.0]
    monkeypatch.setattr(rate_limit.time, "time", lambda: now[0])

    def advance(seconds):
        now[0] += seconds

    return advance


def test_throttle_waits_for_next_window_once_budget_is_spent(sleep, clock):
    sleep.side_effect = clock
    for _ in range(3):
        throttle("bucket", 3)
    sleep.assert_not_called()

    throttle("bucket", 3)

    sleep.assert_called_once_with(60.0)


@pytest.mark.usefixtures("clock")
def test_session_waits_for_reset_below_half_quota(mocked_responses, sleep):
    mocked_responses.add(
        "GET",
        "https://api.github.com/rate",
        headers={
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "2499",
            "X-RateLimit-Reset": "900",
        },
    )
    mocked_responses.add(
        "GET",
        "https://api.github.com/rate",
        headers={
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "2500",
            "X-RateLimit-Reset": "900",
        },
    )
    session = ThrottledSession("bucket", 100)

    session.get("https://api.github.com/rate")
    sleep.assert_called_once_with(301.0)

    sleep.reset_mock()
    session.get("https://api.github.com/rate")
    sleep.assert_not_called()
