from __future__ import annotations

import ast
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research.signal_observation.csv_loader import load_ohlcv_csv
from research.signal_observation.models import BtcScore, Direction, ObservationStatus, SetupId
from research.signal_observation.setup_a import detect_setup_a


FIXTURE_DIR = Path("tests/fixtures/signal_observation")


def _known_context():
    candles = load_ohlcv_csv(FIXTURE_DIR / "known_breakout_retest_4h.csv")
    breakout = candles[-1]
    seed = candles[:-1]
    start_time = breakout.timestamp - timedelta(hours=4 * 48)
    full_base = []
    for index in range(48):
        source = seed[index % len(seed)]
        full_base.append(
            type(source)(
                timestamp=start_time + timedelta(hours=4 * index),
                open=source.open,
                high=source.high,
                low=source.low,
                close=source.close,
                volume=source.volume,
            )
        )
    return full_base + [breakout]


def _known_trigger():
    return load_ohlcv_csv(FIXTURE_DIR / "known_breakout_retest_1h.csv")


def _detect_known():
    return detect_setup_a(
        _known_context(),
        _known_trigger(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    )


def test_known_breakout_retest_fixture_produces_valid_long_observation() -> None:
    observations = _detect_known()

    assert len(observations) == 1
    assert observations[0].status is ObservationStatus.VALID


def test_returned_observation_has_expected_setup_fields_and_decimal_risk() -> None:
    observation = _detect_known()[0]

    assert observation.setup_id is SetupId.A
    assert observation.direction is Direction.LONG
    assert observation.status is ObservationStatus.VALID
    assert observation.context_timeframe == "4H"
    assert observation.trigger_timeframe == "1H"
    assert isinstance(observation.entry_price_theoretical, Decimal)
    assert isinstance(observation.stop_price_theoretical, Decimal)
    assert isinstance(observation.target_price_theoretical, Decimal)
    assert isinstance(observation.initial_r, Decimal)
    assert observation.outcome_window_candles == 24

    assert observation.entry_price_theoretical is not None
    assert observation.stop_price_theoretical is not None
    assert observation.target_price_theoretical is not None
    initial_r = observation.entry_price_theoretical - observation.stop_price_theoretical
    assert observation.initial_r == initial_r
    assert observation.target_price_theoretical == (
        observation.entry_price_theoretical + (Decimal("2") * initial_r)
    )


def test_detector_passes_custom_btc_score_to_observation() -> None:
    observations = detect_setup_a(
        _known_context(),
        _known_trigger(),
        symbol="ETHUSDT",
        source_exchange="fixture",
        btc_score=BtcScore.BULLISH,
    )

    assert observations[0].btc_score is BtcScore.BULLISH


def test_detector_returns_no_signal_when_retest_is_missing() -> None:
    trigger = [
        candle
        for candle in _known_trigger()
        if candle.timestamp.hour not in {10, 11, 12}
    ]

    assert detect_setup_a(
        _known_context(),
        trigger,
        symbol="BTCUSDT",
        source_exchange="fixture",
    ) == []


def test_detector_returns_no_signal_when_breakout_volume_is_too_low() -> None:
    context = list(_known_context())
    breakout = context[-1]
    context[-1] = type(breakout)(
        timestamp=breakout.timestamp,
        open=breakout.open,
        high=breakout.high,
        low=breakout.low,
        close=breakout.close,
        volume=Decimal("1000"),
    )

    assert detect_setup_a(
        context,
        _known_trigger(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    ) == []


def test_detector_returns_no_signal_with_fewer_than_three_range_touches() -> None:
    context = []
    known_context = _known_context()
    for index, candle in enumerate(known_context):
        keep_boundary_touch = index < 2 or index == len(known_context) - 1
        if not keep_boundary_touch:
            context.append(
                type(candle)(
                    timestamp=candle.timestamp,
                    open=min(candle.open, Decimal("102.00")),
                    high=Decimal("102.00"),
                    low=candle.low,
                    close=min(candle.close, Decimal("102.00")),
                    volume=candle.volume,
                )
            )
        else:
            context.append(candle)

    assert detect_setup_a(
        context,
        _known_trigger(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    ) == []


def test_detector_returns_no_signal_when_breakout_body_is_too_small() -> None:
    context = list(_known_context())
    breakout = context[-1]
    context[-1] = type(breakout)(
        timestamp=breakout.timestamp,
        open=Decimal("105.70"),
        high=breakout.high,
        low=breakout.low,
        close=breakout.close,
        volume=breakout.volume,
    )

    assert detect_setup_a(
        context,
        _known_trigger(),
        symbol="BTCUSDT",
        source_exchange="fixture",
    ) == []


def test_short_direction_is_not_silently_accepted() -> None:
    with pytest.raises(NotImplementedError, match="short"):
        detect_setup_a(
            _known_context(),
            _known_trigger(),
            symbol="BTCUSDT",
            source_exchange="fixture",
            direction=Direction.SHORT,
        )


def test_detector_does_not_import_exchange_api_network_or_private_libraries() -> None:
    setup_a_path = (
        Path(__file__).parent.parent.parent
        / "research"
        / "signal_observation"
        / "setup_a.py"
    )
    text = setup_a_path.read_text()
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


def test_detector_uses_no_float_literals_for_price_or_r_calculations() -> None:
    setup_a_path = (
        Path(__file__).parent.parent.parent
        / "research"
        / "signal_observation"
        / "setup_a.py"
    )
    tree = ast.parse(setup_a_path.read_text())

    for node in ast.walk(tree):
        assert not isinstance(node, ast.Constant) or not isinstance(node.value, float)
        assert not isinstance(node, ast.Name) or node.id != "float"
