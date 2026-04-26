from __future__ import annotations

from datetime import datetime, timezone


def _as_aware_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp


def is_stale(timestamp: datetime, threshold_seconds: int) -> bool:
    timestamp = _as_aware_utc(timestamp)
    age = (datetime.now(timezone.utc) - timestamp).total_seconds()
    return age > threshold_seconds
