"""Tests for research.simcore.quality — constitution §5 data quality validator."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research.simcore.candles import Candle
from research.simcore.quality import QualityReport, assess_candles, passes, to_json_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = datetime(2024, 1, 1, tzinfo=UTC)
_1H = timedelta(hours=1)


def _candle(ts: datetime, volume: str = "100") -> Candle:
    return Candle(
        timestamp=ts,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal(volume),
    )


def _hourly(n: int) -> list[Candle]:
    """n consecutive hourly candles starting at _BASE."""
    return [_candle(_BASE + _1H * i) for i in range(n)]


# ---------------------------------------------------------------------------
# Test 1 — clean 10-bar set passes
# ---------------------------------------------------------------------------

def test_clean_set_passes() -> None:
    # 10 hourly bars, 0h–9h; no gaps, no duplicates, all volumes > 0.
    # total_bars=10, expected_bars=round(9h/1h)+1=10, missing_bars=0
    # missing_fraction = Decimal(0)/Decimal(10) = Decimal("0")
    candles = _hourly(10)
    report = assess_candles(candles, expected_duration=_1H)

    assert report.total_bars == 10
    assert report.expected_bars == 10
    assert report.missing_bars == 0
    assert report.missing_fraction == Decimal("0")
    assert report.gaps == ()
    assert report.duplicate_timestamps == 0
    assert report.non_monotonic == 0
    assert report.zero_volume_bars == 0

    ok, reasons = passes(report)
    assert ok is True
    assert reasons == []


# ---------------------------------------------------------------------------
# Test 2 — one missing bar: gap recorded, fraction exact
# ---------------------------------------------------------------------------

def test_one_missing_bar_gap_and_fraction() -> None:
    # 9 candles at hours 0,1,2,3,4,6,7,8,9 (bar 5 missing).
    # span = 9h = 32400s; dur = 3600s
    # expected_bars = round(32400/3600) + 1 = 9 + 1 = 10
    # missing_bars = 10 - 9 = 1
    # missing_fraction = Decimal(1) / Decimal(10) = Decimal("0.1")
    # Gap between candles[4] (4h) and candles[5] (6h): delta=7200s > 1.5*3600=5400
    #   bars_missing = round(7200/3600) - 1 = 2 - 1 = 1
    #   gap_start = _BASE + 4h
    timestamps = [_BASE + _1H * i for i in range(10) if i != 5]
    candles = [_candle(ts) for ts in timestamps]
    report = assess_candles(candles, expected_duration=_1H)

    assert report.total_bars == 9
    assert report.expected_bars == 10
    assert report.missing_bars == 1
    assert report.missing_fraction == Decimal("1") / Decimal("10")
    assert len(report.gaps) == 1
    assert report.gaps[0] == (_BASE + timedelta(hours=4), 1)

    ok, reasons = passes(report, max_missing_fraction=Decimal("0.01"))
    # missing_fraction 10% > 1% threshold → fail
    assert ok is False
    assert any("missing_fraction" in r for r in reasons)

    ok_loose, _ = passes(report, max_missing_fraction=Decimal("0.15"))
    assert ok_loose is True


# ---------------------------------------------------------------------------
# Test 3 — duplicate timestamp fails regardless of threshold
# ---------------------------------------------------------------------------

def test_duplicate_timestamp_always_fails() -> None:
    # 3 candles: hours 0, 1, 1 (duplicate at hour 1).
    # duplicate_timestamps = 1 (one extra occurrence of the repeated timestamp).
    candles = [
        _candle(_BASE + _1H * 0),
        _candle(_BASE + _1H * 1),
        _candle(_BASE + _1H * 1),  # duplicate
    ]
    report = assess_candles(candles, expected_duration=_1H)

    assert report.duplicate_timestamps == 1
    ok, reasons = passes(report)
    assert ok is False
    assert any("duplicate" in r for r in reasons)


# ---------------------------------------------------------------------------
# Test 4 — zero-volume bars counted; passing by default, failing when disallowed
# ---------------------------------------------------------------------------

def test_zero_volume_counted_but_passing_by_default() -> None:
    # 10 hourly bars, bar 3 has volume=0.
    candles = _hourly(10)
    candles[3] = Candle(
        timestamp=candles[3].timestamp,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("0"),
    )
    report = assess_candles(candles, expected_duration=_1H)

    assert report.zero_volume_bars == 1

    ok_default, _ = passes(report)  # allow_zero_volume=True by default
    assert ok_default is True

    ok_strict, reasons_strict = passes(report, allow_zero_volume=False)
    assert ok_strict is False
    assert any("zero-volume" in r for r in reasons_strict)


# ---------------------------------------------------------------------------
# Test 5 — CLI writes the JSON artifact next to the CSV
# ---------------------------------------------------------------------------

def test_cli_writes_quality_json_artifact(tmp_path: Path) -> None:
    csv_content = (
        "timestamp,open,high,low,close,volume\n"
        "2024-01-01T00:00:00+00:00,100,101,99,100,50\n"
        "2024-01-01T01:00:00+00:00,100,101,99,100,50\n"
        "2024-01-01T02:00:00+00:00,100,101,99,100,50\n"
        "2024-01-01T03:00:00+00:00,100,101,99,100,50\n"
        "2024-01-01T04:00:00+00:00,100,101,99,100,50\n"
    )
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    from research.signal_observation.run_data_quality import main

    exit_code = main([str(csv_file)])
    assert exit_code == 0

    artifact_path = tmp_path / "data.csv.quality.json"
    assert artifact_path.exists()

    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert data["total_bars"] == 5
    assert data["missing_bars"] == 0
    assert "dataset" in data
    assert "generated_at" in data
