import time

import superrequests
from django.core.cache import cache

from django_wtf.core.task_metrics import record_rate_limit_wait

WINDOW_SECONDS = 60


def throttle(bucket: str, requests_per_minute: int) -> None:
    """Block until a request slot is free in the bucket's shared per-minute budget."""
    while True:
        now = time.time()
        key = f"ratelimit:{bucket}:{int(now // WINDOW_SECONDS)}"
        cache.add(key, 0, timeout=WINDOW_SECONDS * 2)
        try:
            count = cache.incr(key)
        except ValueError:
            # Key evicted between add and incr; don't block on a cache hiccup.
            return
        # None when the cache backend swallows connection errors.
        if count is None or count <= requests_per_minute:
            return
        pause = WINDOW_SECONDS - now % WINDOW_SECONDS
        record_rate_limit_wait(bucket, "budget", pause)
        time.sleep(pause)


class ThrottledSession(superrequests.Session):
    """
    A session that throttles every request against a shared budget, and pauses
    until the quota resets once the API reports less than half of it remaining.
    """

    def __init__(self, bucket: str, requests_per_minute: int, **kwargs):
        super().__init__(**kwargs)
        self.bucket = bucket
        self.requests_per_minute = requests_per_minute

    def request(self, method, url, *args, **kwargs):  # pylint: disable=arguments-differ
        throttle(self.bucket, self.requests_per_minute)
        response = super().request(method, url, *args, **kwargs)
        self._wait_for_quota(response)
        return response

    def _wait_for_quota(self, response):
        headers = response.headers
        try:
            limit = int(headers["X-RateLimit-Limit"])
            remaining = int(headers["X-RateLimit-Remaining"])
            reset = int(headers["X-RateLimit-Reset"])
        except (KeyError, ValueError):
            return
        if remaining >= limit / 2:
            return
        pause = max(0.0, reset - time.time()) + 1
        record_rate_limit_wait(self.bucket, "quota", pause)
        time.sleep(pause)
