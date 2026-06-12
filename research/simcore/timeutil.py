from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median
from typing import Sequence

from research.simcore.candles import Candle


def bar_duration(candles: Sequence[Candle]) -> timedelta:
    """Compute bar duration as the median of consecutive timestamp deltas.

    Isolated missing bars (a single doubled delta) are tolerated. Raises
    ValueError if fewer than 2 candles or if >5% of deltas deviate >1% from
    the median (truly inconsistent data is loud, not silent).
    """
    if len(candles) < 2:
        raise ValueError(
            f"at least 2 candles required to compute bar duration, got {len(candles)}"
        )
    deltas_sec = [
        (candles[i + 1].timestamp - candles[i].timestamp).total_seconds()
        for i in range(len(candles) - 1)
    ]
    med = median(deltas_sec)
    if med <= 0:
        raise ValueError(f"median bar duration is non-positive: {med}s")
    deviations = [abs(d - med) / med for d in deltas_sec]
    bad_count = sum(1 for dev in deviations if dev > 0.01)
    bad_fraction = bad_count / len(deviations)
    if bad_fraction > 0.05:
        raise ValueError(
            f"bar duration inconsistent: {bad_count}/{len(deviations)} deltas "
            f"({bad_fraction:.1%}) deviate >1% from median {med}s"
        )
    return timedelta(seconds=med)


def decision_time(candle: Candle, duration: timedelta) -> datetime:
    """Bar CLOSE time = open time + bar duration (constitution §3.1)."""
    return candle.timestamp + duration


def label_session(candle: Candle, duration: timedelta) -> str:
    """Session label derived from decision_time, not open time (constitution §3.1)."""
    from research.signal_observation.sessions import session_label  # avoid circular at import time

    return session_label(decision_time(candle, duration))
