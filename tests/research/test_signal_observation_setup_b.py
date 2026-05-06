from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.setup_a import detect_setup_a
from research.signal_observation.setup_b import (
    OUTCOME_WINDOW_CANDLES,
    PERCENT_BUFFER,
    Pivot,
    PivotKind,
    SignalDirection,
    calculate_stop_buffer,
    detect_setup_b,
    determine_trend_state,
    evaluate_multi_r_outcomes,
    find_pivots,
    is_pullback_depth_valid,
)


def test_pivot_detection_with_n_2_finds_strict_pivots() -> None:
    candles = _long_setup_candles()

    pivots = find_pivots(candles, left=2, right=2)

    assert any(pivot.kind is PivotKind.HIGH and pivot.index == 6 for pivot in pivots)
    assert any(pivot.kind is PivotKind.HIGH and pivot.index == 10 for pivot in pivots)
    assert any(pivot.kind is PivotKind.LOW and pivot.index == 4 for pivot in pivots)
    assert any(pivot.kind is PivotKind.LOW and pivot.index == 8 for pivot in pivots)


def test_uptrend_detection_requires_two_higher_highs_and_two_higher_lows() -> None:
    pivots = [
        _pivot(PivotKind.LOW, 1, "90"),
        _pivot(PivotKind.HIGH, 2, "100"),
        _pivot(PivotKind.LOW, 3, "95"),
        _pivot(PivotKind.HIGH, 4, "110"),
    ]

    assert determine_trend_state(pivots, current_index=10) == "uptrend"


def test_downtrend_detection_requires_two_lower_highs_and_two_lower_lows() -> None:
    pivots = [
        _pivot(PivotKind.HIGH, 1, "120"),
        _pivot(PivotKind.LOW, 2, "100"),
        _pivot(PivotKind.HIGH, 3, "115"),
        _pivot(PivotKind.LOW, 4, "90"),
    ]

    assert determine_trend_state(pivots, current_index=10) == "downtrend"


def test_pullback_depth_between_point_30_and_point_70_is_accepted() -> None:
    assert is_pullback_depth_valid(Decimal("0.30"))
    assert is_pullback_depth_valid(Decimal("0.50"))
    assert is_pullback_depth_valid(Decimal("0.70"))


def test_pullback_depth_below_point_30_is_rejected() -> None:
    assert not is_pullback_depth_valid(Decimal("0.29"))


def test_pullback_depth_above_point_70_is_rejected() -> None:
    assert not is_pullback_depth_valid(Decimal("0.71"))


def test_long_bos_requires_close_above_pullback_high_and_rejects_wick_only() -> None:
    observations = detect_setup_b(
        _long_setup_candles(),
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
    )
    wick_only = detect_setup_b(
        _long_setup_candles(bos_close=Decimal("107.5"), bos_high=Decimal("109")),
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
    )

    assert len(observations) == 1
    assert wick_only == []


def test_short_bos_requires_close_below_pullback_low_and_rejects_wick_only() -> None:
    observations = detect_setup_b(
        _short_setup_candles(),
        symbol="BTCUSDT",
        direction=SignalDirection.SHORT,
    )
    wick_only_candles = _short_setup_candles(bos_close=Decimal("104"), bos_low=Decimal("102"))[:15]
    wick_only = detect_setup_b(
        wick_only_candles,
        symbol="BTCUSDT",
        direction=SignalDirection.SHORT,
    )

    assert len(observations) == 1
    assert wick_only == []


def test_entry_uses_bos_close_and_records_next_bar_open() -> None:
    observation = detect_setup_b(
        _long_setup_candles(),
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
    )[0]

    assert observation.entry_price == Decimal("109")
    assert observation.next_bar_open == Decimal("110")
    assert observation.entry_time == observation.bos_time
    assert observation.signal_hour_utc == observation.signal_time.hour


def test_trend_age_swings_counts_confirmed_swings_not_candles() -> None:
    observation = detect_setup_b(
        _long_setup_candles(),
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
    )[0]

    assert observation.trend_age_swings == 4


def test_stop_buffer_uses_minimum_of_percent_entry_and_atr() -> None:
    entry = Decimal("100")

    percent_buffer, atr_buffer, chosen_buffer = calculate_stop_buffer(
        entry_price=entry,
        atr_at_entry=Decimal("2"),
    )

    assert percent_buffer == entry * PERCENT_BUFFER
    assert atr_buffer == Decimal("2")
    assert chosen_buffer == Decimal("0.500")


def test_multi_r_outcome_records_1r_1_5r_and_2r() -> None:
    candles = _long_setup_candles(outcome_high=Decimal("130"))
    observation = detect_setup_b(candles, symbol="BTCUSDT", direction=SignalDirection.LONG)[0]

    assert observation.outcome_1r == "win"
    assert observation.outcome_1_5r == "win"
    assert observation.outcome_2r == "win"
    assert observation.mfe_2r is not None
    assert observation.mae_2r is not None


def test_target_resolution_mae_mfe_stop_at_resolution_bar() -> None:
    outcomes = evaluate_multi_r_outcomes(
        _outcome_candles(
            [
                ("100", "102", "99", "101"),
                ("101", "104", "98", "103"),
                ("103", "105", "98", "105"),
                ("105", "130", "90", "120"),
            ]
        ),
        entry_index=0,
        entry_price=Decimal("100"),
        stop=Decimal("95"),
        initial_r=Decimal("5"),
        direction=SignalDirection.LONG,
    )

    outcome = outcomes[Decimal("1")]
    assert outcome.outcome == "win"
    assert outcome.bars_to_resolution == 3
    assert outcome.mfe_r == Decimal("1")
    assert outcome.mae_r == Decimal("-0.4")


def test_stop_resolution_mae_mfe_stop_at_resolution_bar() -> None:
    outcomes = evaluate_multi_r_outcomes(
        _outcome_candles(
            [
                ("100", "102", "99", "101"),
                ("101", "103", "95", "96"),
                ("96", "130", "90", "120"),
            ]
        ),
        entry_index=0,
        entry_price=Decimal("100"),
        stop=Decimal("95"),
        initial_r=Decimal("5"),
        direction=SignalDirection.LONG,
    )

    outcome = outcomes[Decimal("1")]
    assert outcome.outcome == "loss"
    assert outcome.bars_to_resolution == 2
    assert outcome.mfe_r == Decimal("0.6")
    assert outcome.mae_r == Decimal("-1")


def test_timeout_creates_flat_outcome() -> None:
    candles = _long_setup_candles(outcome_high=Decimal("112"), outcome_low=Decimal("104"))
    observation = detect_setup_b(candles, symbol="BTCUSDT", direction=SignalDirection.LONG)[0]

    assert observation.outcome_1r == "flat"
    assert observation.bars_to_resolution_1r == OUTCOME_WINDOW_CANDLES


def test_timeout_mae_mfe_use_full_timeout_window() -> None:
    outcomes = evaluate_multi_r_outcomes(
        _outcome_candles(
            [
                ("100", "102", "99", "101"),
                ("101", "103", "98", "102"),
                ("102", "104", "96", "103"),
            ]
        ),
        entry_index=0,
        entry_price=Decimal("100"),
        stop=Decimal("95"),
        initial_r=Decimal("5"),
        direction=SignalDirection.LONG,
        outcome_window_candles=3,
    )

    outcome = outcomes[Decimal("1")]
    assert outcome.outcome == "flat"
    assert outcome.mfe_r == Decimal("0.8")
    assert outcome.mae_r == Decimal("-0.8")


def test_same_candle_stop_first_remains_explicit() -> None:
    outcomes = evaluate_multi_r_outcomes(
        _outcome_candles([("100", "106", "94", "101")]),
        entry_index=0,
        entry_price=Decimal("100"),
        stop=Decimal("95"),
        initial_r=Decimal("5"),
        direction=SignalDirection.LONG,
    )

    outcome = outcomes[Decimal("1")]
    assert outcome.outcome == "loss"
    assert outcome.bars_to_resolution == 1


def test_evaluate_multi_r_outcomes_handles_short_target() -> None:
    candles = _short_setup_candles(outcome_low=Decimal("40"))
    observation = detect_setup_b(candles, symbol="BTCUSDT", direction=SignalDirection.SHORT)[0]

    assert observation.outcome_1r == "win"
    assert observation.outcome_1_5r == "win"
    assert observation.outcome_2r == "win"


def test_setup_b_does_not_import_network_or_runtime_libraries() -> None:
    repo_root = Path(__file__).parent.parent.parent
    text = (repo_root / "research" / "signal_observation" / "setup_b.py").read_text()

    forbidden_tokens = (
        "urllib",
        "requests",
        "http.client",
        "socket",
        "libs.exchange",
        "execution_service",
        "risk_engine",
        "orchestrator",
        "position_manager",
        "kill_switch",
    )
    for token in forbidden_tokens:
        assert token not in text


def test_setup_b_uses_no_float_literals_for_price_or_r_calculations() -> None:
    repo_root = Path(__file__).parent.parent.parent
    tree = ast.parse((repo_root / "research" / "signal_observation" / "setup_b.py").read_text())

    for node in ast.walk(tree):
        assert not isinstance(node, ast.Constant) or not isinstance(node.value, float)
        assert not isinstance(node, ast.Name) or node.id != "float"


def test_setup_a_detector_behavior_remains_unaffected() -> None:
    assert detect_setup_a([], [], symbol="BTCUSDT", source_exchange="fixture") == []


def _pivot(kind: PivotKind, index: int, price: str) -> Pivot:
    timestamp = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=4 * index)
    return Pivot(
        kind=kind,
        index=index,
        confirmation_index=index + 2,
        timestamp=timestamp,
        confirmation_time=timestamp + timedelta(hours=8),
        price=Decimal(price),
    )


def _long_setup_candles(
    *,
    bos_close: Decimal = Decimal("109"),
    bos_high: Decimal = Decimal("110"),
    outcome_high: Decimal = Decimal("112"),
    outcome_low: Decimal = Decimal("104"),
) -> list[Candle]:
    rows = [
        ("90", "92", "89", "91"),
        ("91", "94", "90", "93"),
        ("93", "96", "92", "95"),
        ("95", "94", "90", "91"),
        ("91", "93", "88", "90"),
        ("90", "96", "89", "95"),
        ("95", "100", "94", "99"),
        ("99", "98", "93", "94"),
        ("94", "96", "92", "95"),
        ("95", "104", "94", "103"),
        ("103", "110", "102", "109"),
        ("107", "108", "104", "105"),
        ("105", "106", "101", "102"),
        ("102", "107", "103", "106"),
        ("106", str(bos_high), "105", str(bos_close)),
    ]
    candles = _candles(rows)
    for index in range(OUTCOME_WINDOW_CANDLES):
        candles.append(
            Candle(
                timestamp=candles[-1].timestamp + timedelta(hours=4),
                open=Decimal("110") if index == 0 else Decimal("109"),
                high=outcome_high,
                low=outcome_low,
                close=Decimal("109"),
                volume=Decimal("100"),
            )
        )
    return candles


def _short_setup_candles(
    *,
    bos_close: Decimal = Decimal("91"),
    bos_low: Decimal = Decimal("90"),
    outcome_high: Decimal = Decimal("96"),
    outcome_low: Decimal = Decimal("88"),
) -> list[Candle]:
    rows = [
        ("130", "131", "128", "129"),
        ("129", "132", "127", "131"),
        ("131", "133", "129", "132"),
        ("132", "130", "123", "124"),
        ("124", "125", "120", "121"),
        ("123", "128", "122", "127"),
        ("127", "129", "121", "122"),
        ("116", "122", "114", "121"),
        ("121", "124", "110", "111"),
        ("111", "118", "110", "117"),
        ("117", "119", "100", "101"),
        ("101", "108", "103", "107"),
        ("107", "111", "104", "110"),
        ("110", "110", "105", "106"),
        ("95", "96", str(bos_low), str(bos_close)),
    ]
    candles = _candles(rows)
    for index in range(OUTCOME_WINDOW_CANDLES):
        candles.append(
            Candle(
                timestamp=candles[-1].timestamp + timedelta(hours=4),
                open=Decimal("90") if index == 0 else Decimal("91"),
                high=outcome_high,
                low=outcome_low,
                close=Decimal("91"),
                volume=Decimal("100"),
            )
        )
    return candles


def _candles(rows: list[tuple[str, str, str, str]]) -> list[Candle]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index, (open_, high, low, close) in enumerate(rows):
        open_decimal = Decimal(open_)
        high_decimal = max(Decimal(high), open_decimal, Decimal(close), Decimal(low))
        low_decimal = min(Decimal(low), open_decimal, Decimal(close), high_decimal)
        candles.append(
            Candle(
                timestamp=start + timedelta(hours=4 * index),
                open=open_decimal,
                high=high_decimal,
                low=low_decimal,
                close=Decimal(close),
                volume=Decimal("100"),
            )
        )
    return candles


def _outcome_candles(rows: list[tuple[str, str, str, str]]) -> list[Candle]:
    return _candles([("100", "100", "100", "100"), *rows])
