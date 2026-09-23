from contextlib import contextmanager
from time import perf_counter

from django_o11y.metrics import counter, histogram

INDEXING_EVENTS = counter(
    "django_wtf_indexing_events_total",
    description="Domain-level indexing events",
    labelnames=("pipeline", "event"),
)

EXTERNAL_API_REQUESTS = counter(
    "django_wtf_external_api_requests_total",
    description="External API calls made by indexing tasks",
    labelnames=("provider", "operation", "status"),
)

EXTERNAL_API_DURATION = histogram(
    "django_wtf_external_api_request_duration_seconds",
    description="External API call duration in seconds",
    labelnames=("provider", "operation"),
)

RATE_LIMIT_WAIT = histogram(
    "django_wtf_rate_limit_wait_seconds",
    description="Time spent waiting on outbound API rate limits",
    labelnames=("bucket", "reason"),
)

VALUE_TRUNCATIONS = counter(
    "django_wtf_ingestion_value_truncations_total",
    description="String values truncated before persistence",
    labelnames=("pipeline", "field", "limit"),
)


def record_indexing_event(pipeline: str, event: str, amount: int = 1) -> None:
    INDEXING_EVENTS.add(amount, {"pipeline": pipeline, "event": event})


def record_value_truncation(
    pipeline: str, field: str, limit: int, amount: int = 1
) -> None:
    VALUE_TRUNCATIONS.add(
        amount,
        {"pipeline": pipeline, "field": field, "limit": str(limit)},
    )


@contextmanager
def observe_external_api(provider: str, operation: str):
    start = perf_counter()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        EXTERNAL_API_REQUESTS.add(
            1,
            {
                "provider": provider,
                "operation": operation,
                "status": status,
            },
        )
        EXTERNAL_API_DURATION.record(
            perf_counter() - start,
            {
                "provider": provider,
                "operation": operation,
            },
        )


def record_rate_limit_wait(bucket: str, reason: str, seconds: float) -> None:
    RATE_LIMIT_WAIT.record(seconds, {"bucket": bucket, "reason": reason})
