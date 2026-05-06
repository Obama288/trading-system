"""UTC session labeling utilities for signal observation research."""

from __future__ import annotations

from datetime import UTC, datetime


def session_label(timestamp: datetime) -> str:
    """Return a coarse UTC trading-session label."""

    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")

    utc_timestamp = timestamp.astimezone(UTC)
    if utc_timestamp.weekday() >= 5:
        return "weekend"

    hour = utc_timestamp.hour
    if hour < 8:
        return "Asia"
    if hour < 13:
        return "Europe"
    if hour < 17:
        return "overlap"
    return "US"
