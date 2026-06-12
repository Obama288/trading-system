from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research.signal_observation.candles import Candle
from research.signal_observation.models import (
    BtcScore,
    Direction,
    ObservationStatus,
    SetupId,
    SignalObservation,
)
from research.signal_observation.outcomes import resolve_outcome


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


def _observation(
    *,
    direction: Direction = Direction.LONG,
    entry: str = "100",
    stop: str = "99",
    target: str = "102",
    initial_r: str = "1",
    entry_time=None,
    outcome_window_candles: int = 3,
) -> SignalObservation:
    resolved_entry_time = entry_time
    if resolved_entry_time is None:
        resolved_entry_time = datetime(2026, 5, 4, tzinfo=UTC)
    return SignalObservation(
        observation_id="obs-001",
        created_at_utc=datetime(2026, 5, 4, tzinfo=UTC),
        source_exchange="fixture",
        symbol="BTCUSDT",
        setup_id=SetupId.A,
        direction=direction,
        context_timeframe="4H",
        trigger_timeframe="1H",
        signal_time=datetime(2026, 5, 4, tzinfo=UTC),
        entry_time_theoretical=resolved_entry_time,
        entry_price_theoretical=Decimal(entry),
        stop_price_theoretical=Decimal(stop),
        target_price_theoretical=Decimal(target),
        initial_r=Decimal(initial_r),
        btc_score=BtcScore.CHOP,
        session_utc_hour=0,
        session_label="Asia",
        status=ObservationStatus.VALID,
        outcome_window_candles=outcome_window_candles,
    )


def test_long_target_hit_before_stop_returns_positive_r_and_target_flag() -> None:
    result = resolve_outcome(
        _observation(),
        [
            _candle(0, "100", "101", "99.50", "100.50"),
            _candle(1, "100.50", "102.20", "100.20", "102"),
        ],
    )

    assert result.final_r == Decimal("2")
    assert result.hit_target_before_stop is True
    assert result.hit_stop_before_target is False
    assert result.resolution_reason == "target"


def test_long_stop_hit_before_target_returns_minus_one_r_and_stop_flag() -> None:
    result = resolve_outcome(
        _observation(),
        [_candle(0, "100", "100.50", "98.80", "99")],
    )

    assert result.final_r == Decimal("-1")
    assert result.hit_stop_before_target is True
    assert result.hit_target_before_stop is False
    assert result.resolution_reason == "stop"


def test_long_same_candle_ambiguity_resolves_stop_first() -> None:
    result = resolve_outcome(
        _observation(),
        [_candle(0, "100", "102.50", "98.50", "101")],
    )

    assert result.final_r == Decimal("-1")
    assert result.hit_stop_before_target is True
    assert result.hit_target_before_stop is False
    assert result.resolution_reason == "stop"


def test_long_window_close_result_when_neither_target_nor_stop_hit() -> None:
    result = resolve_outcome(
        _observation(),
        [
            _candle(0, "100", "101", "99.50", "100.50"),
            _candle(1, "100.50", "101.50", "100", "101.25"),
        ],
    )

    assert result.final_r == Decimal("1.25")
    assert result.resolution_reason == "window_close"


def test_long_mfe_and_mae_are_calculated_over_window() -> None:
    # entry_price=100, stop=99, target=110, initial_r=1
    # FLAT outcome (target 110 never reached):
    #   Bar 1 (entry, no gap): h=101.50 < 110, l=99.25 > 99 → no exit
    #   Bar 2: o=100.50 (no gap), h=101.80 < 110, l=99.50 > 99 → no exit → FLAT
    # MAE over [entry..exit]: min_low=min(99.25,99.50)=99.25 → (100−99.25)/1=0.75
    # MFE over [entry..exit]: max_high=max(101.50,101.80)=101.80 → (101.80−100)/1=1.80
    # Note: mae_r is non-negative per simcore §5.4 (was −0.75 in pre-migration code)
    result = resolve_outcome(
        _observation(target="110", outcome_window_candles=2),
        [
            _candle(0, "100", "101.50", "99.25", "100.50"),
            _candle(1, "100.50", "101.80", "99.50", "100.75"),
        ],
    )

    assert result.mfe_r == Decimal("1.80")
    assert result.mae_r == Decimal("0.75")


def test_short_target_hit_before_stop_returns_positive_r_and_target_flag() -> None:
    result = resolve_outcome(
        _observation(
            direction=Direction.SHORT,
            entry="100",
            stop="101",
            target="98",
            initial_r="1",
        ),
        [_candle(0, "100", "100.50", "97.80", "98")],
    )

    assert result.final_r == Decimal("2")
    assert result.hit_target_before_stop is True
    assert result.hit_stop_before_target is False
    assert result.resolution_reason == "target"


def test_short_stop_hit_before_target_returns_minus_one_r_and_stop_flag() -> None:
    result = resolve_outcome(
        _observation(
            direction=Direction.SHORT,
            entry="100",
            stop="101",
            target="98",
            initial_r="1",
        ),
        [_candle(0, "100", "101.20", "99.50", "101")],
    )

    assert result.final_r == Decimal("-1")
    assert result.hit_stop_before_target is True
    assert result.hit_target_before_stop is False
    assert result.resolution_reason == "stop"


def test_short_same_candle_ambiguity_resolves_stop_first() -> None:
    result = resolve_outcome(
        _observation(
            direction=Direction.SHORT,
            entry="100",
            stop="101",
            target="98",
            initial_r="1",
        ),
        [_candle(0, "100", "101.50", "97.50", "99")],
    )

    assert result.final_r == Decimal("-1")
    assert result.hit_stop_before_target is True
    assert result.hit_target_before_stop is False
    assert result.resolution_reason == "stop"


def test_no_candles_after_entry_returns_no_candles_result() -> None:
    result = resolve_outcome(
        _observation(entry_time=datetime(2026, 5, 5, tzinfo=UTC)),
        [_candle(0, "100", "101", "99", "100")],
    )

    assert result.final_r is None
    assert result.mfe_r is None
    assert result.mae_r is None
    assert result.hit_target_before_stop is False
    assert result.hit_stop_before_target is False
    assert result.resolution_reason == "no_candles_after_entry"


def test_missing_required_observation_fields_raise_value_error() -> None:
    observation = _observation()
    observation.entry_time_theoretical = None

    with pytest.raises(ValueError, match="entry_time_theoretical"):
        resolve_outcome(observation, [_candle(0, "100", "101", "99", "100")])


def test_outcomes_module_has_no_network_or_exchange_imports() -> None:
    text = Path("research/signal_observation/outcomes.py").read_text()
    forbidden_tokens = (
        "requests",
        "httpx",
        "aiohttp",
        "websocket",
        "websockets",
        "ccxt",
        "socket",
        "libs.exchange",
    )

    for token in forbidden_tokens:
        assert token not in text


def test_outcomes_module_uses_no_float_literals_for_price_or_r_calculations() -> None:
    tree = ast.parse(Path("research/signal_observation/outcomes.py").read_text())

    for node in ast.walk(tree):
        assert not isinstance(node, ast.Constant) or not isinstance(node.value, float)
        assert not isinstance(node, ast.Name) or node.id != "float"
