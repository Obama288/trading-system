"""Deterministic indicator utilities for signal observation research."""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from .candles import Candle


def true_range(current: Candle, previous: Candle | None) -> Decimal:
    """Calculate true range for one candle."""

    high_low = current.high - current.low
    if previous is None:
        return high_low
    high_close = abs(current.high - previous.close)
    low_close = abs(current.low - previous.close)
    return max(high_low, high_close, low_close)


def atr(candles: Sequence[Candle], period: int = 14) -> list[Decimal | None]:
    """Calculate ATR using Wilder smoothing."""

    if period <= 0:
        raise ValueError("period must be positive")
    if not candles:
        raise ValueError("candles must not be empty")

    true_ranges = [
        true_range(candle, candles[index - 1] if index > 0 else None)
        for index, candle in enumerate(candles)
    ]
    values: list[Decimal | None] = [None] * len(candles)
    if len(candles) < period:
        return values

    previous_atr = sum(true_ranges[:period]) / Decimal(period)
    values[period - 1] = previous_atr

    for index in range(period, len(candles)):
        current_atr = (
            (previous_atr * Decimal(period - 1)) + true_ranges[index]
        ) / Decimal(period)
        values[index] = current_atr
        previous_atr = current_atr

    return values


def ema(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    """Calculate EMA with a simple-average seed."""

    if period <= 0:
        raise ValueError("period must be positive")
    if not values:
        raise ValueError("values must not be empty")

    output: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return output

    previous_ema = sum(values[:period]) / Decimal(period)
    output[period - 1] = previous_ema
    multiplier = Decimal(2) / Decimal(period + 1)

    for index in range(period, len(values)):
        current_ema = ((values[index] - previous_ema) * multiplier) + previous_ema
        output[index] = current_ema
        previous_ema = current_ema

    return output


def pivot_highs(candles: Sequence[Candle], left: int = 2, right: int = 2) -> list[bool]:
    """Return strict pivot-high markers."""

    if left <= 0:
        raise ValueError("left must be positive")
    if right <= 0:
        raise ValueError("right must be positive")

    markers = [False] * len(candles)
    for index in range(left, len(candles) - right):
        high = candles[index].high
        left_highs = (candles[offset].high for offset in range(index - left, index))
        right_highs = (
            candles[offset].high for offset in range(index + 1, index + right + 1)
        )
        markers[index] = all(high > value for value in left_highs) and all(
            high > value for value in right_highs
        )
    return markers


def pivot_lows(candles: Sequence[Candle], left: int = 2, right: int = 2) -> list[bool]:
    """Return strict pivot-low markers."""

    if left <= 0:
        raise ValueError("left must be positive")
    if right <= 0:
        raise ValueError("right must be positive")

    markers = [False] * len(candles)
    for index in range(left, len(candles) - right):
        low = candles[index].low
        left_lows = (candles[offset].low for offset in range(index - left, index))
        right_lows = (
            candles[offset].low for offset in range(index + 1, index + right + 1)
        )
        markers[index] = all(low < value for value in left_lows) and all(
            low < value for value in right_lows
        )
    return markers
