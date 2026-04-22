from __future__ import annotations

from datetime import datetime, timezone


def classify_session(timestamp: datetime) -> str:
    hour = timestamp.astimezone(timezone.utc).hour
    if 0 <= hour < 8:
        return "asia"
    if 8 <= hour < 13:
        return "london"
    if 13 <= hour < 17:
        return "london_ny_overlap"
    return "ny"
