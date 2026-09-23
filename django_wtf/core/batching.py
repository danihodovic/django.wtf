from collections.abc import Callable, Iterable
from itertools import batched

from celery.exceptions import SoftTimeLimitExceeded
from django.core.cache import cache
from django_o11y.logging.utils import get_logger

from django_wtf.core.task_metrics import record_indexing_event

logger = get_logger()

# Long enough to cover a slow run, short enough that a batch killed before it
# could decrement doesn't block the pipeline for more than a night.
PENDING_TIMEOUT = 36 * 60 * 60


def _pending_key(pipeline: str) -> str:
    return f"pending_batches:{pipeline}"


def dispatch_in_batches(task, values: Iterable, size: int, pipeline: str) -> None:
    """Enqueue `task` once per batch of `values`, unless the previous run is unfinished."""
    key = _pending_key(pipeline)
    pending = cache.get(key) or 0
    if pending > 0:
        logger.warning("indexing_run_skipped_previous_pending", pipeline=pipeline)
        record_indexing_event(pipeline, "skipped_overlap")
        return
    batches = [list(batch) for batch in batched(values, size)]
    cache.set(key, len(batches), timeout=PENDING_TIMEOUT)
    for batch in batches:
        task.delay(batch, pipeline)


def run_batch(fn: Callable, items: Iterable, pipeline: str) -> None:
    """Call `fn` on every item, so one failure doesn't drop the rest of the batch."""
    try:
        for item in items:
            try:
                fn(item)
            except SoftTimeLimitExceeded:
                raise
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception(
                    "indexing_batch_item_failed", pipeline=pipeline, item=item
                )
                record_indexing_event(pipeline, "error")
    finally:
        try:
            cache.decr(_pending_key(pipeline))
        except ValueError:
            pass
