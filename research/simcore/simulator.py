from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Sequence

from research.simcore.candles import Candle
from research.simcore.models import (
    Direction,
    FillPolicy,
    InvalidTrade,
    TargetSim,
    TradeSim,
    TradeSpec,
)
from research.simcore.timeutil import decision_time, label_session

_ZERO = Decimal("0")


def _target_price(entry_price: Decimal, initial_r: Decimal, target_r: Decimal, direction: Direction) -> Decimal:
    if direction == Direction.LONG:
        return entry_price + target_r * initial_r
    return entry_price - target_r * initial_r


def _signed_r(exit_price: Decimal, entry_price: Decimal, initial_r: Decimal, direction: Direction) -> Decimal:
    if direction == Direction.LONG:
        return (exit_price - entry_price) / initial_r
    return (entry_price - exit_price) / initial_r


def _simulate_one_target(
    candles: Sequence[Candle],
    entry_index: int,
    entry_price: Decimal,
    initial_r: Decimal,
    target_r: Decimal,
    target_price: Decimal,
    stop_price: Decimal,
    direction: Direction,
    outcome_window_bars: int,
) -> TargetSim:
    """Resolve a single target-R independently over the outcome window.

    Per spec §5.3:
      - Step 1: gap check on bar open (skipped for the entry bar).
        Both beyond stop AND target (degenerate) → treat as stop.
      - Step 2: intrabar stop checked BEFORE target (constitution §3.4).
      - Step 3: window exhausted → flat, mark-to-market at last close.
    MAE/MFE computed over candles[entry_index..exit_index] inclusive (§5.4).
    """
    window = candles[entry_index : entry_index + outcome_window_bars]

    exit_index = entry_index
    exit_price = _ZERO
    outcome = "flat"
    gap_exit = False
    resolved = False

    for bar_offset, bar in enumerate(window):
        bar_index = entry_index + bar_offset
        is_entry_bar = bar_offset == 0

        if not is_entry_bar:
            # Step 1: gap check — entry bar is already validated in §5.1.
            if direction == Direction.LONG:
                gap_stop = bar.open <= stop_price
                gap_target = bar.open >= target_price
            else:
                gap_stop = bar.open >= stop_price
                gap_target = bar.open <= target_price

            if gap_stop:
                # Conservative: stop takes priority even in the degenerate case.
                exit_index = bar_index
                exit_price = bar.open
                outcome = "loss"
                gap_exit = True
                resolved = True
                break
            if gap_target:
                exit_index = bar_index
                exit_price = bar.open
                outcome = "win"
                gap_exit = True
                resolved = True
                break

        # Step 2: intrabar — stop evaluated before target (constitution §3.4).
        if direction == Direction.LONG:
            stop_hit = bar.low <= stop_price
            target_hit = bar.high >= target_price
        else:
            stop_hit = bar.high >= stop_price
            target_hit = bar.low <= target_price

        if stop_hit:
            exit_index = bar_index
            exit_price = stop_price
            outcome = "loss"
            resolved = True
            break
        if target_hit:
            exit_index = bar_index
            exit_price = target_price
            outcome = "win"
            resolved = True
            break

    if not resolved:
        # Step 3: flat — mark-to-market at the last window bar's close (§5.3).
        exit_index = entry_index + len(window) - 1
        exit_price = window[-1].close
        outcome = "flat"

    final_r_gross = _signed_r(exit_price, entry_price, initial_r, direction)

    # MAE/MFE over candles[entry_index..exit_index] inclusive (§5.4).
    resolution_bars = candles[entry_index : exit_index + 1]
    if direction == Direction.LONG:
        min_low = min(b.low for b in resolution_bars)
        max_high = max(b.high for b in resolution_bars)
        mae_r = max(_ZERO, (entry_price - min_low) / initial_r)
        mfe_r = max(_ZERO, (max_high - entry_price) / initial_r)
    else:
        max_high = max(b.high for b in resolution_bars)
        min_low = min(b.low for b in resolution_bars)
        mae_r = max(_ZERO, (max_high - entry_price) / initial_r)
        mfe_r = max(_ZERO, (entry_price - min_low) / initial_r)

    return TargetSim(
        target_r=target_r,
        target_price=target_price,
        outcome=outcome,
        exit_price=exit_price,
        exit_index=exit_index,
        bars_to_resolution=exit_index - entry_index + 1,
        gap_exit=gap_exit,
        final_r_gross=final_r_gross,
        mae_r=mae_r,
        mfe_r=mfe_r,
    )


def simulate_trade(
    candles: Sequence[Candle],
    spec: TradeSpec,
    duration: timedelta,
) -> TradeSim | InvalidTrade:
    """Simulate a trade according to spec §5.

    `duration` is the bar duration (compute once with timeutil.bar_duration).
    Returns TradeSim on success, InvalidTrade with a reason code on failure.
    """
    # Validation 1: window_non_positive — basic param check first.
    if spec.outcome_window_bars <= 0:
        return InvalidTrade(spec=spec, reason="window_non_positive")

    # Validation 2: no_entry_bar (NEXT_BAR_OPEN only, §5.1).
    if spec.fill == FillPolicy.NEXT_BAR_OPEN:
        if spec.signal_index + 1 >= len(candles):
            return InvalidTrade(spec=spec, reason="no_entry_bar")
        entry_index = spec.signal_index + 1
        entry_price = candles[entry_index].open
    else:  # SIGNAL_CLOSE
        entry_index = spec.signal_index
        entry_price = candles[entry_index].close

    entry_time = decision_time(candles[spec.signal_index], duration)

    # Validation 3: non_positive_r.
    initial_r = abs(entry_price - spec.stop_price)
    if initial_r <= _ZERO:
        return InvalidTrade(spec=spec, reason="non_positive_r")

    # Validation 4: entry_gap_through_stop.
    entry_bar = candles[entry_index]
    if spec.direction == Direction.LONG:
        if entry_bar.open <= spec.stop_price:
            return InvalidTrade(spec=spec, reason="entry_gap_through_stop")
    else:
        if entry_bar.open >= spec.stop_price:
            return InvalidTrade(spec=spec, reason="entry_gap_through_stop")

    # Validation 5: entry_gap_through_target (nearest = smallest target_r).
    nearest_target_r = min(spec.target_r_values)
    nearest_target_price = _target_price(entry_price, initial_r, nearest_target_r, spec.direction)
    if spec.direction == Direction.LONG:
        if entry_bar.open >= nearest_target_price:
            return InvalidTrade(spec=spec, reason="entry_gap_through_target")
    else:
        if entry_bar.open <= nearest_target_price:
            return InvalidTrade(spec=spec, reason="entry_gap_through_target")

    session = label_session(candles[spec.signal_index], duration)

    targets: dict[Decimal, TargetSim] = {}
    for target_r in spec.target_r_values:
        t_price = _target_price(entry_price, initial_r, target_r, spec.direction)
        targets[target_r] = _simulate_one_target(
            candles=candles,
            entry_index=entry_index,
            entry_price=entry_price,
            initial_r=initial_r,
            target_r=target_r,
            target_price=t_price,
            stop_price=spec.stop_price,
            direction=spec.direction,
            outcome_window_bars=spec.outcome_window_bars,
        )

    return TradeSim(
        spec=spec,
        entry_index=entry_index,
        entry_time=entry_time,
        entry_price=entry_price,
        initial_r=initial_r,
        session=session,
        targets=targets,
    )


# Alias — multi-target is handled by simulate_trade via spec.target_r_values.
simulate_multi_target = simulate_trade
