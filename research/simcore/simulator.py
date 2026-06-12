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
    skip_entry_bar_gap: bool = True,
) -> TargetSim:
    """Resolve a single target-R independently over the outcome window.

    Per spec §5.3:
      - Step 1: gap check on bar open (skipped for the entry bar when
        skip_entry_bar_gap=True, i.e. NEXT_BAR_OPEN where bar open IS entry).
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
        # For NEXT_BAR_OPEN the entry bar's open IS the entry price (already validated).
        # For SIGNAL_CLOSE all resolution bars get the gap check, including the first.
        is_entry_bar = bar_offset == 0 and skip_entry_bar_gap

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

    # Fill-policy entry setup + fill-specific availability check.
    if spec.fill == FillPolicy.NEXT_BAR_OPEN:
        if spec.signal_index + 1 >= len(candles):
            return InvalidTrade(spec=spec, reason="no_entry_bar")
        entry_index = spec.signal_index + 1
        entry_price = candles[entry_index].open
        skip_first_gap = True          # entry bar open IS the entry price
    else:  # SIGNAL_CLOSE
        # Resolution window starts at signal_index+1; the signal bar's own
        # range is look-ahead for a close fill (v1.1 amendment).
        if spec.signal_index + 1 >= len(candles):
            return InvalidTrade(spec=spec, reason="no_resolution_bars")
        entry_index = spec.signal_index + 1
        entry_price = candles[spec.signal_index].close
        skip_first_gap = False         # first resolution bar gets the gap check

    entry_time = decision_time(candles[spec.signal_index], duration)

    # Validation: non_positive_r.
    initial_r = abs(entry_price - spec.stop_price)
    if initial_r <= _ZERO:
        return InvalidTrade(spec=spec, reason="non_positive_r")

    # Validation: entry_gap_through_stop (NEXT_BAR_OPEN only).
    # For SIGNAL_CLOSE there is no entry bar open to compare; any gap on
    # the first resolution bar is handled inside _simulate_one_target.
    if spec.fill == FillPolicy.NEXT_BAR_OPEN:
        entry_bar = candles[entry_index]
        if spec.direction == Direction.LONG:
            if entry_bar.open <= spec.stop_price:
                return InvalidTrade(spec=spec, reason="entry_gap_through_stop")
        else:
            if entry_bar.open >= spec.stop_price:
                return InvalidTrade(spec=spec, reason="entry_gap_through_stop")

    # Validation: incomplete_window — candle array too short (v1.1 amendment).
    if entry_index + spec.outcome_window_bars > len(candles):
        return InvalidTrade(spec=spec, reason="incomplete_window")

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
            skip_entry_bar_gap=skip_first_gap,
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
