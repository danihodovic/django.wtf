from unittest.mock import Mock

from django.core.cache import cache

from .batching import dispatch_in_batches, run_batch


def test_dispatch_in_batches_splits_values():
    task = Mock()
    dispatch_in_batches(task, iter(range(5)), 2, "pipeline")

    assert [call.args for call in task.delay.call_args_list] == [
        ([0, 1], "pipeline"),
        ([2, 3], "pipeline"),
        ([4], "pipeline"),
    ]
    assert cache.get("pending_batches:pipeline") == 3


def test_dispatch_in_batches_skips_while_previous_run_is_pending():
    task = Mock()
    dispatch_in_batches(task, iter(range(4)), 2, "pipeline")
    run_batch(Mock(), [0, 1], "pipeline")
    dispatch_in_batches(task, iter(range(4)), 2, "pipeline")

    assert task.delay.call_count == 2

    run_batch(Mock(), [2, 3], "pipeline")
    dispatch_in_batches(task, iter(range(4)), 2, "pipeline")

    assert task.delay.call_count == 4


def test_run_batch_continues_after_failed_item():
    fn = Mock(side_effect=[ValueError("boom"), None, None])
    run_batch(fn, ["a", "b", "c"], "pipeline")

    assert [call.args for call in fn.call_args_list] == [("a",), ("b",), ("c",)]
