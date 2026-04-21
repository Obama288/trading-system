from __future__ import annotations

from datetime import datetime, timezone


def is_stale(timestamp: datetime, threshold_seconds: int) -> bool:
    age = (datetime.now(timezone.utc) - timestamp).total_seconds()
    return age > threshold_seconds
