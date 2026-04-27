from datetime import datetime, timedelta, timezone

from apps.market_data.domain.freshness import is_stale


def test_is_stale_false_for_timezone_aware_recent_timestamp():
    ts = datetime.now(timezone.utc) - timedelta(seconds=5)

    assert is_stale(ts, threshold_seconds=30) is False


def test_is_stale_true_for_timezone_aware_old_timestamp():
    ts = datetime.now(timezone.utc) - timedelta(seconds=60)

    assert is_stale(ts, threshold_seconds=30) is True


def test_is_stale_false_for_naive_recent_timestamp():
    ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=5)

    assert is_stale(ts, threshold_seconds=30) is False


def test_is_stale_true_for_naive_old_timestamp():
    ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=60)

    assert is_stale(ts, threshold_seconds=30) is True
