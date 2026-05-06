from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from research.signal_observation.sessions import session_label


def test_session_labels_for_weekday_utc_hours() -> None:
    monday = datetime(2026, 5, 4, tzinfo=UTC)

    assert session_label(monday.replace(hour=0)) == "Asia"
    assert session_label(monday.replace(hour=8)) == "Europe"
    assert session_label(monday.replace(hour=13)) == "overlap"
    assert session_label(monday.replace(hour=17)) == "US"


def test_weekend_overrides_weekday_session_windows() -> None:
    saturday = datetime(2026, 5, 9, 13, tzinfo=UTC)

    assert session_label(saturday) == "weekend"


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        session_label(datetime(2026, 5, 4, 13))


def test_timezone_aware_non_utc_timestamp_is_normalized() -> None:
    moscow = timezone(timedelta(hours=3))
    timestamp = datetime(2026, 5, 4, 16, tzinfo=moscow)

    assert session_label(timestamp) == "overlap"
