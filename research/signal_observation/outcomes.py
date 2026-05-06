"""Simulated R outcome tracking for signal observations."""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from .candles import Candle
from .models import Direction, OutcomeResult, SignalObservation


def resolve_outcome(
    observation: SignalObservation,
    trigger_candles: Sequence[Candle],
) -> OutcomeResult:
    """Resolve one observation outcome from local trigger candles."""

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

    window = [
        candle for candle in trigger_candles if candle.timestamp >= entry_time
    ][:outcome_window_candles]

    if not window:
        return OutcomeResult(
            outcome_window_candles=outcome_window_candles,
            resolution_reason="no_candles_after_entry",
        )

    if observation.direction is Direction.LONG:
        return _resolve_long(
            window=window,
            outcome_window_candles=outcome_window_candles,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            initial_r=initial_r,
        )
    if observation.direction is Direction.SHORT:
        return _resolve_short(
            window=window,
            outcome_window_candles=outcome_window_candles,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            initial_r=initial_r,
        )
    raise ValueError(f"unsupported direction: {observation.direction!r}")


def _resolve_long(
    *,
    window: Sequence[Candle],
    outcome_window_candles: int,
    entry_price: Decimal,
    stop_price: Decimal,
    target_price: Decimal,
    initial_r: Decimal,
) -> OutcomeResult:
    mfe_r = max((candle.high - entry_price) / initial_r for candle in window)
    mae_r = min((candle.low - entry_price) / initial_r for candle in window)

    for candle in window:
        stop_hit = candle.low <= stop_price
        target_hit = candle.high >= target_price
        if stop_hit:
            return OutcomeResult(
                outcome_window_candles=outcome_window_candles,
                mfe_r=mfe_r,
                mae_r=mae_r,
                final_r=Decimal("-1"),
                hit_stop_before_target=True,
                resolution_reason="stop",
            )
        if target_hit:
            return OutcomeResult(
                outcome_window_candles=outcome_window_candles,
                mfe_r=mfe_r,
                mae_r=mae_r,
                final_r=(target_price - entry_price) / initial_r,
                hit_target_before_stop=True,
                resolution_reason="target",
            )

    return OutcomeResult(
        outcome_window_candles=outcome_window_candles,
        mfe_r=mfe_r,
        mae_r=mae_r,
        final_r=(window[-1].close - entry_price) / initial_r,
        resolution_reason="window_close",
    )


def _resolve_short(
    *,
    window: Sequence[Candle],
    outcome_window_candles: int,
    entry_price: Decimal,
    stop_price: Decimal,
    target_price: Decimal,
    initial_r: Decimal,
) -> OutcomeResult:
    mfe_r = max((entry_price - candle.low) / initial_r for candle in window)
    mae_r = min((entry_price - candle.high) / initial_r for candle in window)

    for candle in window:
        stop_hit = candle.high >= stop_price
        target_hit = candle.low <= target_price
        if stop_hit:
            return OutcomeResult(
                outcome_window_candles=outcome_window_candles,
                mfe_r=mfe_r,
                mae_r=mae_r,
                final_r=Decimal("-1"),
                hit_stop_before_target=True,
                resolution_reason="stop",
            )
        if target_hit:
            return OutcomeResult(
                outcome_window_candles=outcome_window_candles,
                mfe_r=mfe_r,
                mae_r=mae_r,
                final_r=(entry_price - target_price) / initial_r,
                hit_target_before_stop=True,
                resolution_reason="target",
            )

    return OutcomeResult(
        outcome_window_candles=outcome_window_candles,
        mfe_r=mfe_r,
        mae_r=mae_r,
        final_r=(entry_price - window[-1].close) / initial_r,
        resolution_reason="window_close",
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
