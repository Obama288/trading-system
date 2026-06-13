"""Setup H — regime-gated TSMOM detector and analysis primitives.

Governed by: research/signal_observation/SETUP_H_PREREGISTRATION.md (LOCKED
2026-06-13). Do not modify the signal definition, regime gate, or cost
constants without a new pre-registration.

Primary metric: mean vol-normalised post-cost return (expectancy_R) for the
gated signal minus the same for the ungated signal, pooled over the discovery
window, non-overlapping rebalance observations.
R unit = ATR20/close per rebalance interval (consistent with Setup C).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Sequence

from research.signal_observation.candles import Candle
from research.signal_observation.indicators import atr as _compute_atr
from research.signal_observation.setup_c_tsmom import (
    close_to_close_return,
    tsmom_direction,
    turnover_units,
)

# ---------------------------------------------------------------------------
# Locked constants (from pre-registration §2.3 and §2.4)
# ---------------------------------------------------------------------------

LOOKBACK: int = 40
ATR_PERIOD: int = 20
MEDIAN_WINDOW: int = 180
REBALANCE_EVERY: int = 6
DISCOVERY_CUTOFF: datetime = datetime(2024, 9, 24, 4, 0, 0, tzinfo=UTC)

COST_BPS: dict[str, Decimal] = {
    "optimistic": Decimal("5"),
    "moderate": Decimal("8"),
    "conservative": Decimal("15"),
}
PRIMARY_COST: str = "moderate"

RANDOM_SEED: int = 69
N_RESAMPLES: int = 1_000

GATE_GATED_MIN: Decimal = Decimal("0.05")    # gated expectancy_R ≥ +0.05R
GATE_DIFF_MIN: Decimal = Decimal("0.05")     # gated - ungated ≥ +0.05R
GATE_SHUFFLED_PCT: int = 95                  # gated must beat shuffled p95

_TINY_VOL_FLOOR: Decimal = Decimal("0.000001")


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class GatedObs:
    """One rebalance-bar observation for gated and ungated TSMOM comparison."""
    symbol: str
    bar_index: int
    timestamp: datetime
    regime: str               # 'LOW' | 'HIGH'
    direction_signal: int     # ±1/0  (TSMOM before gate; 0 only if return = 0)
    direction_gated: int      # 0 if HIGH-VOL; else direction_signal
    interval_return: Decimal  # close[i+rebalance_every] / close[i] - 1
    vol_proxy: Decimal        # ATR20/close, floored at _TINY_VOL_FLOOR
    turnover_ungated: int     # position-change units vs previous ungated dir
    turnover_gated: int       # position-change units vs previous gated dir


# ---------------------------------------------------------------------------
# Pure helper functions (importable for tests)
# ---------------------------------------------------------------------------

def classify_regime(vol_proxy: Decimal, median: Decimal) -> str:
    """'LOW' if vol_proxy < median else 'HIGH'."""
    return "LOW" if vol_proxy < median else "HIGH"


def trailing_median(
    series: list[Decimal | None],
    i: int,
    window: int,
) -> Decimal | None:
    """Median of series[max(0, i-window+1):i+1] excluding Nones.

    Returns None when fewer than `window` non-None values are available.
    """
    start = i - window + 1
    if start < 0:
        return None
    window_vals: list[Decimal] = [v for v in series[start : i + 1] if v is not None]
    if len(window_vals) < window:
        return None
    sorted_vals = sorted(window_vals)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return sorted_vals[mid]
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal("2")


def _vol_proxy(
    candles: Sequence[Candle],
    atr_vals: list[Decimal | None],
    i: int,
) -> Decimal | None:
    v = atr_vals[i]
    c = candles[i].close
    if v is None or c <= Decimal("0"):
        return None
    proxy = v / c
    return proxy if proxy > Decimal("0") else None


# ---------------------------------------------------------------------------
# Core detector
# ---------------------------------------------------------------------------

def build_gated_obs(
    candles: Sequence[Candle],
    *,
    symbol: str,
    cutoff: datetime = DISCOVERY_CUTOFF,
    lookback: int = LOOKBACK,
    atr_period: int = ATR_PERIOD,
    median_window: int = MEDIAN_WINDOW,
    rebalance_every: int = REBALANCE_EVERY,
) -> list[GatedObs]:
    """Build per-symbol discovery-window observations for gated/ungated TSMOM.

    Only rebalance bars satisfying ALL of the following are included:
    - open_time[i] ≤ cutoff  (bar in discovery window)
    - open_time[i + rebalance_every] ≤ cutoff  (outcome bar in discovery window)
    - trailing median is computable (enough history)
    - vol_proxy at bar i is valid (ATR defined, close > 0)
    """
    n = len(candles)
    if n == 0:
        return []
    atr_vals = _compute_atr(candles, period=atr_period)

    vol_proxy_series: list[Decimal | None] = [
        _vol_proxy(candles, atr_vals, i) for i in range(n)
    ]

    # Warmup: need both lookback and enough bars for the trailing median.
    # ATR is defined from index atr_period-1; need median_window bars of it.
    warmup = max(lookback, atr_period - 1 + median_window - 1)

    result: list[GatedObs] = []
    prev_dir_ungated = 0
    prev_dir_gated = 0

    for i in range(warmup, n - rebalance_every, rebalance_every):
        if candles[i].timestamp > cutoff:
            break
        if candles[i + rebalance_every].timestamp > cutoff:
            break

        med = trailing_median(vol_proxy_series, i, median_window)
        if med is None:
            continue

        vp = vol_proxy_series[i]
        if vp is None:
            continue
        vol = max(vp, _TINY_VOL_FLOOR)

        regime = classify_regime(vp, med)

        lr = close_to_close_return(candles, i, lookback)
        direction_signal = tsmom_direction(lr)
        direction_gated = direction_signal if regime == "LOW" else 0

        close_now = candles[i].close
        if close_now <= Decimal("0"):
            continue
        interval_return = candles[i + rebalance_every].close / close_now - Decimal("1")

        tu_ungated = turnover_units(prev_dir_ungated, direction_signal)
        tu_gated = turnover_units(prev_dir_gated, direction_gated)

        result.append(GatedObs(
            symbol=symbol,
            bar_index=i,
            timestamp=candles[i].timestamp,
            regime=regime,
            direction_signal=direction_signal,
            direction_gated=direction_gated,
            interval_return=interval_return,
            vol_proxy=vol,
            turnover_ungated=tu_ungated,
            turnover_gated=tu_gated,
        ))

        prev_dir_ungated = direction_signal
        prev_dir_gated = direction_gated

    return result


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def obs_expectancy(
    obs: list[GatedObs],
    *,
    gated: bool,
    cost_bps: Decimal,
) -> Decimal | None:
    """Mean vol-normalised post-cost return (expectancy_R) across obs.

    Return = (direction × interval_return - turnover × cost_bps/10000) / vol_proxy
    All observations included; flats contribute 0 gross and 0 or 1 turnover.
    Returns None when obs is empty.
    """
    if not obs:
        return None
    values: list[Decimal] = []
    for o in obs:
        direction = o.direction_gated if gated else o.direction_signal
        turnover = o.turnover_gated if gated else o.turnover_ungated
        gross = Decimal(direction) * o.interval_return
        cost = Decimal(turnover) * cost_bps / Decimal("10000")
        net_vt = (gross - cost) / o.vol_proxy
        values.append(net_vt)
    return sum(values, Decimal("0")) / Decimal(len(values))


def obs_expectancy_scenarios(
    obs: list[GatedObs],
    *,
    gated: bool,
) -> dict[str, Decimal | None]:
    """Expectancy under each cost scenario."""
    return {
        scenario: obs_expectancy(obs, gated=gated, cost_bps=bps)
        for scenario, bps in COST_BPS.items()
    }


# ---------------------------------------------------------------------------
# Shuffled-regime baseline (§2.4)
# ---------------------------------------------------------------------------

def shuffled_regime_baseline(
    obs_by_symbol: dict[str, list[GatedObs]],
    *,
    cost_bps: Decimal = COST_BPS[PRIMARY_COST],
    seed: int = RANDOM_SEED,
    n_resamples: int = N_RESAMPLES,
) -> list[float]:
    """Distribution of pooled gated expectancy under random regime selection.

    Per symbol: the same count of active (LOW-VOL) bars as the true regime
    gate gives is selected randomly from all that symbol's rebalance bars.
    Turnover tracking is maintained per-symbol across the sequence.
    Returns n_resamples mean vol-normalised expectancy values (as floats).
    """
    # Pre-extract float arrays per symbol for speed.
    sym_data: dict[str, tuple[list[int], list[float], list[float], int]] = {}
    for sym, obs in obs_by_symbol.items():
        if not obs:
            continue
        signals = [o.direction_signal for o in obs]
        returns = [float(o.interval_return) for o in obs]
        vols = [float(o.vol_proxy) for o in obs]
        n_active = sum(1 for o in obs if o.direction_gated != 0)
        sym_data[sym] = (signals, returns, vols, n_active)

    cost_float = float(cost_bps) / 10_000.0
    rng = random.Random(seed)
    results: list[float] = []

    for _ in range(n_resamples):
        all_vt: list[float] = []
        for _sym, (signals, returns, vols, n_active) in sym_data.items():
            n = len(signals)
            if n == 0 or n_active == 0:
                # No positions for this symbol in this resample.
                all_vt.extend(
                    (0.0 - 0.0) / vols[j] if vols[j] > 0 else 0.0
                    for j in range(n)
                )
                continue
            active_set: set[int] = set(rng.sample(range(n), min(n_active, n)))
            prev_dir = 0
            for j in range(n):
                direction = signals[j] if j in active_set else 0
                if direction == prev_dir:
                    tu = 0
                elif prev_dir == 0 or direction == 0:
                    tu = 1
                else:
                    tu = 2
                prev_dir = direction
                gross = direction * returns[j]
                cost_raw = tu * cost_float
                vt = (gross - cost_raw) / vols[j] if vols[j] > 0 else (gross - cost_raw)
                all_vt.append(vt)

        results.append(sum(all_vt) / len(all_vt) if all_vt else 0.0)

    return results


def percentile_of(value: float, distribution: list[float]) -> float:
    """Fraction of distribution values strictly below value, as percent (0-100)."""
    if not distribution:
        return 0.0
    below = sum(1 for v in distribution if v < value)
    return 100.0 * below / len(distribution)


def _pct(distribution: list[float], pct: float) -> float:
    """p-th percentile of distribution (floor index)."""
    if not distribution:
        return 0.0
    s = sorted(distribution)
    idx = max(0, int(len(s) * pct / 100) - 1)
    return s[idx]
