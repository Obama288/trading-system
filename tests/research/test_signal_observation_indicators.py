from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research.signal_observation.candles import Candle
from research.signal_observation.indicators import (
    atr,
    ema,
    pivot_highs,
    pivot_lows,
    true_range,
)


def _candle(
    index: int,
    open_: str,
    high: str,
    low: str,
    close: str,
) -> Candle:
    return Candle(
        timestamp=datetime(2026, 5, 4, tzinfo=UTC) + timedelta(hours=index),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("100"),
    )


def test_true_range_with_no_previous_candle() -> None:
    candle = _candle(0, "10", "14", "9", "12")

    assert true_range(candle, None) == Decimal("5")


def test_true_range_with_previous_close_gap() -> None:
    previous = _candle(0, "20", "21", "19", "20")
    current = _candle(1, "12", "14", "10", "13")

    assert true_range(current, previous) == Decimal("10")


def test_atr_returns_same_length_initial_none_and_first_average() -> None:
    candles = [
        _candle(0, "10", "12", "9", "11"),
        _candle(1, "11", "13", "10", "12"),
        _candle(2, "12", "16", "11", "15"),
        _candle(3, "15", "17", "14", "16"),
    ]

    values = atr(candles, period=3)

    assert len(values) == len(candles)
    assert values[:2] == [None, None]
    assert values[2] == Decimal("11") / Decimal("3")
    assert values[3] == (values[2] * Decimal("2") + Decimal("3")) / Decimal("3")


def test_atr_rejects_invalid_period_and_empty_input() -> None:
    with pytest.raises(ValueError, match="period"):
        atr([_candle(0, "10", "12", "9", "11")], period=0)
    with pytest.raises(ValueError, match="empty"):
        atr([], period=14)


def test_ema_returns_same_length_initial_none_and_first_average() -> None:
    values = [Decimal("10"), Decimal("12"), Decimal("14"), Decimal("16")]

    result = ema(values, period=3)

    assert len(result) == len(values)
    assert result[:2] == [None, None]
    assert result[2] == Decimal("12")
    assert result[3] == Decimal("14")


def test_ema_rejects_invalid_period_and_empty_input() -> None:
    with pytest.raises(ValueError, match="period"):
        ema([Decimal("10")], period=0)
    with pytest.raises(ValueError, match="empty"):
        ema([], period=14)


def test_pivot_highs_finds_strict_pivot_and_ignores_equal_highs() -> None:
    candles = [
        _candle(0, "10", "10", "9", "9"),
        _candle(1, "10", "12", "9", "11"),
        _candle(2, "10", "15", "9", "14"),
        _candle(3, "10", "12", "9", "11"),
        _candle(4, "10", "10", "9", "9"),
        _candle(5, "10", "15", "9", "14"),
        _candle(6, "10", "15", "9", "14"),
        _candle(7, "10", "11", "9", "10"),
    ]

    assert pivot_highs(candles, left=1, right=1) == [
        False,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
    ]


def test_pivot_lows_finds_strict_pivot_and_ignores_equal_lows() -> None:
    candles = [
        _candle(0, "10", "12", "10", "11"),
        _candle(1, "10", "12", "8", "11"),
        _candle(2, "10", "12", "5", "11"),
        _candle(3, "10", "12", "8", "11"),
        _candle(4, "10", "12", "10", "11"),
        _candle(5, "10", "12", "5", "11"),
        _candle(6, "10", "12", "5", "11"),
        _candle(7, "10", "12", "9", "11"),
    ]

    assert pivot_lows(candles, left=1, right=1) == [
        False,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
    ]


def test_pivot_functions_reject_invalid_left_or_right() -> None:
    candles = [_candle(0, "10", "12", "9", "11")]

    with pytest.raises(ValueError, match="left"):
        pivot_highs(candles, left=0)
    with pytest.raises(ValueError, match="right"):
        pivot_lows(candles, right=0)


def test_indicators_module_uses_no_float_literals_or_annotations() -> None:
    tree = ast.parse(Path("research/signal_observation/indicators.py").read_text())

    for node in ast.walk(tree):
        assert not isinstance(node, ast.Constant) or not isinstance(node.value, float)
        assert not isinstance(node, ast.Name) or node.id != "float"
