"""Hand-built fixture tests for setup_e_detector.py.

All expected values are derived analytically — no oracle / simulation.
See comments for each test for the derivation.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from research.signal_observation.setup_e_detector import (
    LiqBar,
    SetupESignal,
    compute_setup_e_stop,
    detect_setup_e_signals,
)
from research.simcore.candles import Candle
from research.simcore.models import Direction

_BASE = datetime(2024, 1, 1, tzinfo=UTC)
_4H = timedelta(hours=4)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _candle(
    i: int,
    o: float,
    h: float,
    l: float,
    c: float,
    vol: float = 1_000.0,
) -> Candle:
    return Candle(
        timestamp=_BASE + i * _4H,
        open=Decimal(str(o)),
        high=Decimal(str(h)),
        low=Decimal(str(l)),
        close=Decimal(str(c)),
        volume=Decimal(str(vol)),
    )


def _liq(i: int, long: float, short: float) -> LiqBar:
    return LiqBar(
        timestamp=_BASE + i * _4H,
        long=Decimal(str(long)),
        short=Decimal(str(short)),
    )


def _flat(n: int) -> tuple[list[Candle], list[LiqBar]]:
    """Flat baseline: close=open=100, high=101, low=99, long-liq=100_000."""
    candles = [_candle(i, 100, 101, 99, 100) for i in range(n)]
    liq = [_liq(i, 100_000, 50_000) for i in range(n)]
    return candles, liq


# ---------------------------------------------------------------------------
# Test 1: cascade detection LONG fires on correct bar
# ---------------------------------------------------------------------------

def test_cascade_long_fires():
    """Cascade bar at 180 with long > p95 and down bar → 1 episode."""
    # Derivation:
    #   window at bar 180 = bars[0..179], all long=100_000 (180 values).
    #   p95: rank = int(180*95/100)-1 = 169. sorted[169] = 100_000.
    #   bar 180 long = 5_000_000 > 100_000 ✓.  close(96) < open(102) ✓.
    #   signal at bar 181: window range(1,181) p25=100_000; long=10_000 < 100_000 ✓.
    n = 190
    candles, liq = _flat(n)
    candles[180] = _candle(180, 102, 103, 93, 96)   # down bar
    liq[180] = _liq(180, 5_000_000, 50_000)
    liq[181] = _liq(181, 10_000, 50_000)

    sigs = detect_setup_e_signals("SYM", candles, liq, Direction.LONG)

    assert len(sigs) == 1
    s = sigs[0]
    assert s.signal_index == 181
    assert s.cascade_index == 180
    assert s.direction == Direction.LONG
    assert s.signal_ts == _BASE + 181 * _4H


# ---------------------------------------------------------------------------
# Test 2: no cascade when bar is not a down bar
# ---------------------------------------------------------------------------

def test_cascade_no_down_bar():
    """Bar with high long-liq but close > open → not a cascade for LONG."""
    n = 190
    candles, liq = _flat(n)
    # Up bar — close > open → not a down bar, no cascade
    candles[180] = _candle(180, 96, 103, 93, 102)   # close=102 > open=96
    liq[180] = _liq(180, 5_000_000, 50_000)
    liq[181] = _liq(181, 10_000, 50_000)

    sigs = detect_setup_e_signals("SYM", candles, liq, Direction.LONG)
    assert sigs == []


# ---------------------------------------------------------------------------
# Test 3: long-liq at exactly the 95th pct threshold does not cascade
# ---------------------------------------------------------------------------

def test_cascade_equal_to_95th_pct_does_not_fire():
    """Strict inequality: long == p95 must NOT cascade (need strictly >)."""
    # Derivation:
    #   Window = bars[0..179] all at 100_000. p95 = 100_000.
    #   Bar 180 with long = 100_000 (equal): 100_000 > 100_000 = False → no cascade.
    #   Bar 180 with long = 100_001 (just over): 100_001 > 100_000 = True → cascade.
    n = 190
    candles, liq = _flat(n)
    candles[180] = _candle(180, 102, 103, 93, 96)   # down bar

    # Test equal — must not fire.
    liq_equal = list(liq)
    liq_equal[180] = _liq(180, 100_000, 50_000)   # exactly at p95
    liq_equal[181] = _liq(181, 10_000, 50_000)
    assert detect_setup_e_signals("SYM", candles, liq_equal, Direction.LONG) == []

    # Test one above — must fire.
    liq_over = list(liq)
    liq_over[180] = _liq(180, 100_001, 50_000)
    liq_over[181] = _liq(181, 10_000, 50_000)
    assert len(detect_setup_e_signals("SYM", candles, liq_over, Direction.LONG)) == 1


# ---------------------------------------------------------------------------
# Test 4: exhaustion fires on the FIRST bar below 25th pct
# ---------------------------------------------------------------------------

def test_exhaustion_fires_on_first_bar():
    """Signal bar must be the FIRST bar below 25th pct, not a later one."""
    # Derivation:
    #   bar 181: long=200_000 → above p25=100_000. No signal.
    #   bar 182: long=10_000  → below p25=100_000. Signal fires here.
    n = 190
    candles, liq = _flat(n)
    candles[180] = _candle(180, 102, 103, 93, 96)
    liq[180] = _liq(180, 5_000_000, 50_000)
    liq[181] = _liq(181, 200_000, 50_000)   # above p25 — no signal yet
    liq[182] = _liq(182, 10_000, 50_000)    # below p25 — signal fires

    sigs = detect_setup_e_signals("SYM", candles, liq, Direction.LONG)

    assert len(sigs) == 1
    assert sigs[0].signal_index == 182   # NOT 181


# ---------------------------------------------------------------------------
# Test 5: no signal if no exhaustion bar found within LOOKAHEAD_CAP bars
# ---------------------------------------------------------------------------

def test_no_signal_if_no_exhaustion_in_lookahead():
    """All 24 bars after cascade have long > p25 → no signal returned."""
    # Derivation:
    #   LOOKAHEAD_CAP=25 → search range(181, 205) = 24 bars (181..204).
    #   p25 at each of those bars ≈ 100_000 (mostly 100k in window).
    #   Setting long=200_000 for bars 181..204 keeps all above p25. No signal.
    n = 210
    candles, liq = _flat(n)
    candles[180] = _candle(180, 102, 103, 93, 96)
    liq[180] = _liq(180, 5_000_000, 50_000)
    for j in range(181, 205):
        liq[j] = _liq(j, 200_000, 50_000)   # all above p25

    sigs = detect_setup_e_signals("SYM", candles, liq, Direction.LONG)
    assert sigs == []


# ---------------------------------------------------------------------------
# Test 6: stop placement LONG — cascade extreme = lowest low, buffer applied
# ---------------------------------------------------------------------------

def test_stop_placement_long():
    """LONG stop = min(low over cascade..signal) - min(0.1%×entry, 0.25×ATR20).

    Hand derivation:
      cascade bar 180: low=93.  signal bar 181: low=99 (flat).
      cascade_extreme = min(93, 99) = 93.
      entry bar 182: open=100.
      ATR computation (Wilder, period=20):
        bars[0..178]: TR = 2  → ATR at index 179 = 2.0.
        bar[180]: TR = max(103-93=10, |103-100|=3, |93-100|=7) = 10.
                  ATR[180] = (2.0×19 + 10)/20 = 48/20 = 2.4.
        bar[181]: prev_close=96. TR = max(101-99=2, |101-96|=5, |99-96|=3) = 5.
                  ATR[181] = (2.4×19 + 5)/20 = 50.6/20 = 2.53.
      buffer = min(0.001×100=0.100, 0.25×2.53=0.6325) = 0.100.
      stop = 93 - 0.100 = 92.900.
    """
    n = 190
    candles, liq = _flat(n)
    candles[180] = _candle(180, 102, 103, 93, 96)
    liq[180] = _liq(180, 5_000_000, 50_000)
    liq[181] = _liq(181, 10_000, 50_000)

    sigs = detect_setup_e_signals("SYM", candles, liq, Direction.LONG)
    assert len(sigs) == 1

    stop = compute_setup_e_stop(candles, sigs[0])
    assert sigs[0].cascade_extreme == Decimal("93")
    assert stop == Decimal("92.9")


# ---------------------------------------------------------------------------
# Test 7: stop placement SHORT — cascade extreme = highest high, buffer added
# ---------------------------------------------------------------------------

def test_stop_placement_short():
    """SHORT stop = max(high over cascade..signal) + min(0.1%×entry, 0.25×ATR20).

    Hand derivation:
      cascade bar 180: short=5M, up bar (close=104>open=98), high=108, low=97.
      signal bar 181: short=10k, flat bar (low=99, high=101).
      cascade_extreme = max(108, 101) = 108.
      entry bar 182: open=100.
      ATR:
        bar[180]: prev_close=100. TR = max(108-97=11, |108-100|=8, |97-100|=3)=11.
                  ATR[180] = (2.0×19 + 11)/20 = 49/20 = 2.45.
        bar[181]: prev_close=104. TR = max(2, |101-104|=3, |99-104|=5) = 5.
                  ATR[181] = (2.45×19 + 5)/20 = 51.55/20 = 2.5775.
      buffer = min(0.001×100=0.100, 0.25×2.5775=0.644375) = 0.100.
      stop = 108 + 0.100 = 108.100.
    """
    n = 190
    candles, liq = _flat(n)
    # SHORT cascade: up bar (close > open), high=108
    candles[180] = _candle(180, 98, 108, 97, 104)
    liq[180] = _liq(180, 50_000, 5_000_000)   # short-liq burst
    liq[181] = _liq(181, 50_000, 10_000)      # short-liq exhaustion

    # p95 of short-liq window at bar 180: window=bars[0..179], all short=50_000.
    # 5_000_000 > 50_000 ✓. Up bar ✓. Cascade fires.
    # p25 of short-liq window at bar 181 ≈ 50_000. 10_000 < 50_000 ✓.

    sigs = detect_setup_e_signals("SYM", candles, liq, Direction.SHORT)
    assert len(sigs) == 1
    s = sigs[0]
    assert s.cascade_extreme == Decimal("108")
    assert s.direction == Direction.SHORT

    stop = compute_setup_e_stop(candles, s)
    assert stop == Decimal("108.1")


# ---------------------------------------------------------------------------
# Test 8: non-overlapping — cascade within episode window is skipped
# ---------------------------------------------------------------------------

def test_non_overlapping_cascade_skipped():
    """Second cascade (bar 181) is skipped because next_allowed = 183 after ep1.

    Setup:
      cascade at 180: signal found at 182 (bar 181 has high liq, not exhaustion).
        → episode 1, next_allowed = 183.
      cascade at 181: ci_a=181 < next_allowed=183 → SKIPPED.
    Result: only 1 episode returned (signal_index=182).
    """
    n = 190
    candles, liq = _flat(n)
    # Cascade at 180
    candles[180] = _candle(180, 102, 103, 93, 96)
    liq[180] = _liq(180, 5_000_000, 50_000)
    # Bar 181 is another cascade (not exhaustion, liq still high)
    candles[181] = _candle(181, 102, 103, 93, 96)   # down bar
    liq[181] = _liq(181, 5_000_000, 50_000)         # high liq — NOT exhaustion
    # Bar 182 is exhaustion for cascade 1
    liq[182] = _liq(182, 10_000, 50_000)

    sigs = detect_setup_e_signals("SYM", candles, liq, Direction.LONG)

    assert len(sigs) == 1
    assert sigs[0].signal_index == 182


# ---------------------------------------------------------------------------
# Test 9: discovery cutoff excludes signal that falls after it
# ---------------------------------------------------------------------------

def test_discovery_cutoff_excludes_signal():
    """Signal at bar 181 is excluded when cutoff = bar 180 timestamp."""
    # cutoff = timestamp of bar 180. signal bar 181 timestamp > cutoff → excluded.
    n = 190
    candles, liq = _flat(n)
    candles[180] = _candle(180, 102, 103, 93, 96)
    liq[180] = _liq(180, 5_000_000, 50_000)
    liq[181] = _liq(181, 10_000, 50_000)

    cutoff = _BASE + 180 * _4H   # bar 180 timestamp

    sigs = detect_setup_e_signals(
        "SYM", candles, liq, Direction.LONG, discovery_cutoff_ts=cutoff
    )
    assert sigs == []

    # With cutoff = bar 181 timestamp, signal IS included.
    cutoff_inclusive = _BASE + 181 * _4H
    sigs2 = detect_setup_e_signals(
        "SYM", candles, liq, Direction.LONG, discovery_cutoff_ts=cutoff_inclusive
    )
    assert len(sigs2) == 1
