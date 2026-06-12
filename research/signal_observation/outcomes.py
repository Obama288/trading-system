"""Simulated R outcome tracking for signal observations.

Phase-3 migration: resolve_outcome now delegates to research.simcore.simulator.
Semantic deltas vs pre-migration code (all expected per SIMCORE_SPEC.md §8):
  - entry_gap_through_stop on the entry bar yields InvalidTrade (was treated as
    a regular stop loss before).
  - MAE/MFE are over the resolution window [entry_index..exit_index], not the
    full outcome window.
  - mae_r is non-negative (adverse excursion in R, always >= 0).
  - gap exits on non-entry bars resolve at bar.open (may give final_r < -1).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Sequence

from .candles import Candle
from .models import Direction, OutcomeResult, SignalObservation
from research.simcore.models import (
    Direction as _SimDirection,
    FillPolicy as _FillPolicy,
    InvalidTrade as _SimInvalidTrade,
    TradeSim as _TradeSim,
    TradeSpec as _TradeSpec,
)
from research.simcore.simulator import simulate_trade as _simulate_trade

_TIMEFRAME_DURATIONS: dict[str, timedelta] = {
    "1H": timedelta(hours=1),
    "4H": timedelta(hours=4),
}
_DEFAULT_DURATION = timedelta(hours=1)


def resolve_outcome(
    observation: SignalObservation,
    trigger_candles: Sequence[Candle],
) -> OutcomeResult:
    """Resolve one observation outcome from local trigger candles.

    Delegates to simcore.simulate_trade. A dummy signal candle is prepended so
    that signal_index=0 and entry_index=1, matching NEXT_BAR_OPEN semantics.
    """
    entry_time = _required("entry_time_theoretical", observation.entry_time_theoretical)
    entry_price = _required_decimal(
        "entry_price_theoretical", observation.entry_price_theoretical
    )
    stop_price = _required_decimal(
        "stop_price_theoretical", observation.stop_price_theoretical
    )
    target_price = _required_decimal(
        "target_price_theoretical", observation.target_price_theoretical
    )
    initial_r = _required_decimal("initial_r", observation.initial_r)
    outcome_window_candles = _required(
        "outcome_window_candles", observation.outcome_window_candles
    )
    if outcome_window_candles <= 0:
        raise ValueError("outcome_window_candles must be positive")
    if initial_r <= Decimal("0"):
        raise ValueError("initial_r must be positive")

    # Select the same window the old code used: candles from entry_time onward,
    # capped at outcome_window_candles to avoid incomplete_window rejection.
    window_candles = [
        c for c in trigger_candles if c.timestamp >= entry_time
    ][:outcome_window_candles]

    if not window_candles:
        return OutcomeResult(
            outcome_window_candles=outcome_window_candles,
            resolution_reason="no_candles_after_entry",
        )

    # Derive target_r from observation fields (setup_a always uses 2R but handle generically).
    if observation.direction is Direction.LONG:
        target_r = (target_price - entry_price) / initial_r
    else:
        target_r = (entry_price - target_price) / initial_r
    if target_r <= Decimal("0"):
        return OutcomeResult(
            outcome_window_candles=outcome_window_candles,
            resolution_reason="no_candles_after_entry",
        )

    duration = _TIMEFRAME_DURATIONS.get(observation.trigger_timeframe, _DEFAULT_DURATION)

    # Prepend a dummy signal candle so entry_index=1 for simcore NEXT_BAR_OPEN.
    # The dummy candle's timestamp is one bar before the entry candle (valid for decision_time).
    dummy_signal = Candle(
        timestamp=window_candles[0].timestamp - duration,
        open=entry_price,
        high=entry_price,
        low=entry_price,
        close=entry_price,
        volume=Decimal("0"),
    )
    sim_candles = [dummy_signal] + list(window_candles)

    spec = _TradeSpec(
        symbol=observation.symbol,
        direction=_SimDirection(observation.direction.value),
        signal_index=0,
        stop_price=stop_price,
        target_r_values=(target_r,),
        outcome_window_bars=len(window_candles),  # exact available count — no incomplete_window
        fill=_FillPolicy.NEXT_BAR_OPEN,
    )
    sim_result = _simulate_trade(sim_candles, spec, duration)
    if isinstance(sim_result, _SimInvalidTrade):
        return OutcomeResult(
            outcome_window_candles=outcome_window_candles,
            resolution_reason="no_candles_after_entry",
        )

    return _sim_to_outcome(sim_result, target_r, outcome_window_candles)


def _sim_to_outcome(sim: _TradeSim, target_r: Decimal, outcome_window_candles: int) -> OutcomeResult:
    t = sim.targets[target_r]
    if t.outcome == "win":
        reason = "target"
        hit_target = True
        hit_stop = False
    elif t.outcome == "loss":
        reason = "stop"
        hit_target = False
        hit_stop = True
    else:
        reason = "window_close"
        hit_target = False
        hit_stop = False
    return OutcomeResult(
        outcome_window_candles=outcome_window_candles,
        mfe_r=t.mfe_r,
        mae_r=t.mae_r,
        final_r=t.final_r_gross,
        hit_target_before_stop=hit_target,
        hit_stop_before_target=hit_stop,
        resolution_reason=reason,
    )


def _required(name: str, value):
    if value is None:
        raise ValueError(f"{name} is required")
    return value


def _required_decimal(name: str, value: Decimal | None) -> Decimal:
    if value is None:
        raise ValueError(f"{name} is required")
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")
    return value
