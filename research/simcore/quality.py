"""Data quality assessment for OHLCV candle series (constitution §5).

Required before any Stage 2+ run; produce as a committed artifact next to the
dataset via run_data_quality.py.

QualityReport JSON artifact format (produced by to_json_dict):
{
  "total_bars": <int>,
  "first_timestamp": "<ISO-8601 UTC string>",
  "last_timestamp": "<ISO-8601 UTC string>",
  "duration_seconds": "<Decimal as string>",
  "expected_bars": <int>,
  "missing_bars": <int>,
  "missing_fraction": "<Decimal as string>",
  "gaps": [{"gap_start": "<ISO-8601 UTC>", "bars_missing": <int>}, ...],
  "duplicate_timestamps": <int>,
  "non_monotonic": <int>,
  "zero_volume_bars": <int>
}
gaps is capped at 100 entries. A gap is a consecutive delta > 1.5x duration;
bars_missing = round(delta/duration) - 1.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Sequence

from research.simcore.candles import Candle
from research.simcore.timeutil import bar_duration as _bar_duration

_GAP_THRESHOLD_MULTIPLIER = Decimal("3") / Decimal("2")  # 1.5
_GAP_CAP = 100


@dataclass(frozen=True, slots=True)
class QualityReport:
    """Immutable quality snapshot for one OHLCV candle series.

    All numeric fields are Decimal or int — no floats.
    gaps: (gap_start_timestamp, bars_missing) pairs, at most 100 entries.
    """

    total_bars: int
    first_timestamp: datetime
    last_timestamp: datetime
    duration_seconds: Decimal
    expected_bars: int
    missing_bars: int
    missing_fraction: Decimal
    gaps: tuple[tuple[datetime, int], ...]
    duplicate_timestamps: int
    non_monotonic: int
    zero_volume_bars: int


def assess_candles(
    candles: Sequence[Candle],
    *,
    expected_duration: timedelta | None = None,
) -> QualityReport:
    """Assess data quality of an OHLCV candle series.

    If expected_duration is None, derives bar duration via timeutil.bar_duration
    (requires >= 2 candles with consistent inter-bar spacing).

    Raises ValueError if candles is empty or if bar_duration cannot be inferred.
    """
    if not candles:
        raise ValueError("candles must not be empty")

    total_bars = len(candles)
    first_ts = candles[0].timestamp
    last_ts = candles[-1].timestamp

    # Duplicate timestamps: count excess occurrences (one per extra copy).
    ts_counts: Counter[datetime] = Counter(c.timestamp for c in candles)
    duplicate_count = sum(count - 1 for count in ts_counts.values() if count > 1)

    # Non-monotonic: consecutive pairs where next timestamp is strictly earlier.
    non_monotonic = sum(
        1 for i in range(len(candles) - 1)
        if candles[i + 1].timestamp < candles[i].timestamp
    )

    # Zero-volume bars.
    zero_vol = sum(1 for c in candles if c.volume == Decimal("0"))

    # Derive or use provided duration.
    if expected_duration is None:
        duration = _bar_duration(candles)
    else:
        duration = expected_duration

    dur_secs = Decimal(str(int(duration.total_seconds())))
    span_secs = Decimal(str(int((last_ts - first_ts).total_seconds())))
    expected_bars = (
        int(round(span_secs / dur_secs)) + 1 if dur_secs > Decimal("0") else 1
    )
    missing_bars = expected_bars - total_bars
    missing_fraction = (
        Decimal(missing_bars) / Decimal(expected_bars)
        if expected_bars > 0
        else Decimal("0")
    )

    # Gap detection: consecutive delta > 1.5x duration, capped at 100 entries.
    threshold_secs = dur_secs * _GAP_THRESHOLD_MULTIPLIER
    gaps: list[tuple[datetime, int]] = []
    for i in range(len(candles) - 1):
        delta_secs = Decimal(
            str((candles[i + 1].timestamp - candles[i].timestamp).total_seconds())
        )
        if delta_secs > threshold_secs:
            bars_missing = int(round(delta_secs / dur_secs)) - 1
            if bars_missing >= 1:
                gaps.append((candles[i].timestamp, bars_missing))
            if len(gaps) >= _GAP_CAP:
                break

    return QualityReport(
        total_bars=total_bars,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        duration_seconds=dur_secs,
        expected_bars=expected_bars,
        missing_bars=missing_bars,
        missing_fraction=missing_fraction,
        gaps=tuple(gaps),
        duplicate_timestamps=duplicate_count,
        non_monotonic=non_monotonic,
        zero_volume_bars=zero_vol,
    )


def passes(
    report: QualityReport,
    *,
    max_missing_fraction: Decimal = Decimal("0.01"),
    allow_zero_volume: bool = True,
) -> tuple[bool, list[str]]:
    """Return (passed, failure_reasons) for the quality report.

    Duplicates and non-monotonic always cause failure regardless of thresholds.
    """
    reasons: list[str] = []

    if report.duplicate_timestamps > 0:
        n = report.duplicate_timestamps
        reasons.append(f"{n} duplicate timestamp{'s' if n != 1 else ''}")

    if report.non_monotonic > 0:
        n = report.non_monotonic
        reasons.append(f"{n} non-monotonic bar{'s' if n != 1 else ''}")

    if report.missing_fraction > max_missing_fraction:
        actual_pct = float(report.missing_fraction * 100)
        limit_pct = float(max_missing_fraction * 100)
        reasons.append(f"missing_fraction {actual_pct:.1f}% > {limit_pct:.1f}%")

    if not allow_zero_volume and report.zero_volume_bars > 0:
        n = report.zero_volume_bars
        reasons.append(f"{n} zero-volume bar{'s' if n != 1 else ''}")

    return (len(reasons) == 0, reasons)


def to_json_dict(report: QualityReport) -> dict:
    """Serialize a QualityReport to a JSON-friendly dict.

    Timestamps are ISO-8601 UTC strings. Decimal fields are strings.
    """
    return {
        "total_bars": report.total_bars,
        "first_timestamp": report.first_timestamp.isoformat(),
        "last_timestamp": report.last_timestamp.isoformat(),
        "duration_seconds": str(report.duration_seconds),
        "expected_bars": report.expected_bars,
        "missing_bars": report.missing_bars,
        "missing_fraction": str(report.missing_fraction),
        "gaps": [
            {"gap_start": ts.isoformat(), "bars_missing": n}
            for ts, n in report.gaps
        ],
        "duplicate_timestamps": report.duplicate_timestamps,
        "non_monotonic": report.non_monotonic,
        "zero_volume_bars": report.zero_volume_bars,
    }
