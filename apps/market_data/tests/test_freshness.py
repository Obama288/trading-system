def test_is_stale_false():
    from datetime import datetime, timedelta, timezone
    from apps.market_data.domain.freshness import is_stale
    ts = datetime.now(timezone.utc) - timedelta(seconds=10)
    assert is_stale(ts, threshold_seconds=30) is False
