"""Tests for research/simcore/timeutil.py (spec Phase 1)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from research.simcore.candles import Candle
from research.simcore.timeutil import bar_duration, decision_time, label_session

BASE_TS = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _c(n: int, hours_offset: int | None = None) -> Candle:
    ts = BASE_TS + timedelta(hours=hours_offset if hours_offset is not None else n * 4)
    return Candle(
        timestamp=ts,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("1000"),
    )


def _candles_h4(n: int) -> list[Candle]:
    """n candles at 4-hour intervals."""
    return [_c(i) for i in range(n)]


# ---------------------------------------------------------------------------
# bar_duration — happy path
# ---------------------------------------------------------------------------

def test_bar_duration_h4_uniform():
    candles = _candles_h4(5)
    assert bar_duration(candles) == timedelta(hours=4)


def test_bar_duration_h1_uniform():
    candles = [
        Candle(
            timestamp=BASE_TS + timedelta(hours=i),
            open=Decimal("100"), high=Decimal("101"),
            low=Decimal("99"),  close=Decimal("100"),
            volume=Decimal("1000"),
        )
        for i in range(6)
    ]
    assert bar_duration(candles) == timedelta(hours=1)


def test_bar_duration_two_candles_minimum():
    candles = _candles_h4(2)
    assert bar_duration(candles) == timedelta(hours=4)


def test_bar_duration_returns_timedelta():
    result = bar_duration(_candles_h4(3))
    assert isinstance(result, timedelta)


# ---------------------------------------------------------------------------
# bar_duration — error cases
# ---------------------------------------------------------------------------

def test_bar_duration_one_candle_raises():
    with pytest.raises(ValueError):
        bar_duration(_candles_h4(1))


def test_bar_duration_empty_raises():
    with pytest.raises((ValueError, IndexError)):
        bar_duration([])


def test_bar_duration_mixed_timeframes_raises():
    # deltas: 4h, 4h, 8h → bad_count=1, bad_fraction=1/3≈33% > 5% → raises
    candles = [
        _c(0, hours_offset=0),
        _c(1, hours_offset=4),
        _c(2, hours_offset=8),
        _c(3, hours_offset=16),  # 8h gap instead of 4h
    ]
    with pytest.raises(ValueError, match="inconsistent"):
        bar_duration(candles)


def test_bar_duration_tolerates_single_missing_bar():
    """100 bars at 4 h except one doubled gap — bad_fraction ≈ 1% < 5% — must not raise."""
    # 99 deltas: 98 × 4h + 1 × 8h (bar 50 is one period late)
    # bad_count=1, bad_fraction=1/99≈1.01% < 5% → returns 4h without raising
    candles: list[Candle] = []
    ts = BASE_TS
    for i in range(100):
        candles.append(Candle(
            timestamp=ts,
            open=Decimal("100"), high=Decimal("101"),
            low=Decimal("99"),  close=Decimal("100"),
            volume=Decimal("1000"),
        ))
        ts += timedelta(hours=8) if i == 49 else timedelta(hours=4)
    result = bar_duration(candles)
    assert result == timedelta(hours=4)


def test_bar_duration_small_deviation_accepted():
    # 1-second jitter on otherwise-4h bars — well within 1%
    # delta0=4h, delta1=4h+1s: deviation=1/14400 ≈ 0.007% < 1%
    candles = [
        Candle(
            timestamp=BASE_TS + timedelta(hours=0),
            open=Decimal("100"), high=Decimal("101"),
            low=Decimal("99"),  close=Decimal("100"),
            volume=Decimal("1000"),
        ),
        Candle(
            timestamp=BASE_TS + timedelta(hours=4),
            open=Decimal("100"), high=Decimal("101"),
            low=Decimal("99"),  close=Decimal("100"),
            volume=Decimal("1000"),
        ),
        Candle(
            timestamp=BASE_TS + timedelta(hours=8, seconds=1),
            open=Decimal("100"), high=Decimal("101"),
            low=Decimal("99"),  close=Decimal("100"),
            volume=Decimal("1000"),
        ),
    ]
    # Should not raise; we just check it returns a timedelta
    result = bar_duration(candles)
    assert isinstance(result, timedelta)


# ---------------------------------------------------------------------------
# decision_time
# ---------------------------------------------------------------------------

def test_decision_time_equals_open_plus_duration():
    candle = _c(0, hours_offset=0)
    dur = timedelta(hours=4)
    assert decision_time(candle, dur) == BASE_TS + timedelta(hours=4)


def test_decision_time_preserves_utc():
    candle = _c(0, hours_offset=12)
    dur = timedelta(hours=1)
    result = decision_time(candle, dur)
    assert result.tzinfo is not None
    assert result == BASE_TS + timedelta(hours=13)


# ---------------------------------------------------------------------------
# label_session
# ---------------------------------------------------------------------------

def test_label_session_asia():
    # open_time=00:00 UTC, bar=4h → decision_time=04:00 UTC → Asia (0-7)
    candle = _c(0, hours_offset=0)
    assert label_session(candle, timedelta(hours=4)) == "Asia"


def test_label_session_europe():
    # open_time=04:00 UTC, bar=4h → decision_time=08:00 UTC → Europe (8-12)
    candle = _c(0, hours_offset=4)
    assert label_session(candle, timedelta(hours=4)) == "Europe"


def test_label_session_overlap():
    # open_time=12:00 UTC, bar=4h → decision_time=16:00 UTC → overlap (13-16)
    candle = _c(0, hours_offset=12)
    assert label_session(candle, timedelta(hours=4)) == "overlap"


def test_label_session_returns_string():
    candle = _c(0, hours_offset=0)
    result = label_session(candle, timedelta(hours=4))
    assert isinstance(result, str)
    assert len(result) > 0
