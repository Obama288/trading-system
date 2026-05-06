from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.setup_b_random_baseline import (
    _distribution_summary,
    _evaluate_random_entry,
    build_bucket_specs,
    run_random_baseline_iterations,
)


def _candle(
    index: int,
    *,
    open_value: str = "100",
    high: str = "105",
    low: str = "95",
    close: str = "100",
) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=4 * index),
        open=Decimal(open_value),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("10"),
    )


def _flat_candles(count: int = 16) -> list[Candle]:
    return [
        _candle(index, open_value="100", high="104", low="96", close="100")
        for index in range(count)
    ]


def _observations() -> list[dict[str, object]]:
    return [
        {
            "symbol": "BTCUSDT",
            "signal_direction": "long",
            "entry_price": "100",
            "stop": "90",
        },
        {
            "symbol": "BTCUSDT",
            "signal_direction": "short",
            "entry_price": "100",
            "stop": "112",
        },
        {
            "symbol": "ETHUSDT",
            "signal_direction": "long",
            "entry_price": "200",
            "stop": "180",
        },
    ]


def _setup_metrics() -> dict[str, object]:
    target_metrics = {
        "1r": {
            "expectancy_r": "0",
            "win_rate": "0.25",
            "flat_rate": "0.25",
            "avg_mae_r": "-0.5",
            "avg_mfe_r": "0.8",
        },
        "1_5r": {
            "expectancy_r": "-0.1",
            "win_rate": "0.20",
            "flat_rate": "0.40",
            "avg_mae_r": "-0.6",
            "avg_mfe_r": "0.9",
        },
        "2r": {
            "expectancy_r": "-0.2",
            "win_rate": "0.10",
            "flat_rate": "0.50",
            "avg_mae_r": "-0.7",
            "avg_mfe_r": "1.0",
        },
    }
    return {"overall": {"all": target_metrics}}


def test_deterministic_seeded_random_selection() -> None:
    candles = {"BTCUSDT": _flat_candles(), "ETHUSDT": _flat_candles()}

    first = run_random_baseline_iterations(
        observations=_observations(),
        candles_by_symbol=candles,
        setup_b_metrics=_setup_metrics(),
        iterations=5,
        seed=123,
    )
    second = run_random_baseline_iterations(
        observations=_observations(),
        candles_by_symbol=candles,
        setup_b_metrics=_setup_metrics(),
        iterations=5,
        seed=123,
    )
    assert first == second


def test_bucket_matching_by_symbol_direction_and_count() -> None:
    specs = build_bucket_specs(_observations())

    assert [(spec.symbol, spec.direction, spec.count) for spec in specs] == [
        ("BTCUSDT", "long", 1),
        ("BTCUSDT", "short", 1),
        ("ETHUSDT", "long", 1),
    ]


def test_long_risk_distance_sets_stop_and_targets() -> None:
    candles = [_candle(0, close="100"), _candle(1, high="111", low="99", close="105")]

    entry = _evaluate_random_entry(
        candles=candles,
        entry_index=0,
        direction="long",
        risk_distance=Decimal("10"),
        timeout_bars=1,
    )

    assert entry["stop"] == Decimal("90")
    assert entry["outcome_1r"] == "win"
    assert entry["outcome_1_5r"] == "flat"


def test_short_risk_distance_sets_stop_and_targets() -> None:
    candles = [_candle(0, close="100"), _candle(1, high="101", low="89", close="95")]

    entry = _evaluate_random_entry(
        candles=candles,
        entry_index=0,
        direction="short",
        risk_distance=Decimal("10"),
        timeout_bars=1,
    )

    assert entry["stop"] == Decimal("110")
    assert entry["outcome_1r"] == "win"
    assert entry["outcome_1_5r"] == "flat"


def test_stop_first_same_candle_rule() -> None:
    candles = [_candle(0, close="100"), _candle(1, high="111", low="89", close="100")]

    long_entry = _evaluate_random_entry(
        candles=candles,
        entry_index=0,
        direction="long",
        risk_distance=Decimal("10"),
        timeout_bars=1,
    )
    short_entry = _evaluate_random_entry(
        candles=candles,
        entry_index=0,
        direction="short",
        risk_distance=Decimal("10"),
        timeout_bars=1,
    )
    assert long_entry["outcome_1r"] == "loss"
    assert short_entry["outcome_1r"] == "loss"


def test_timeout_flat() -> None:
    candles = [_candle(0, close="100"), _candle(1, high="104", low="96", close="100")]

    entry = _evaluate_random_entry(
        candles=candles,
        entry_index=0,
        direction="long",
        risk_distance=Decimal("10"),
        timeout_bars=1,
    )

    assert entry["outcome_1r"] == "flat"
    assert entry["bars_to_resolution_1r"] == 1


def test_random_baseline_summary_percentiles_and_flags() -> None:
    candles = {"BTCUSDT": _flat_candles(), "ETHUSDT": _flat_candles()}

    analysis = run_random_baseline_iterations(
        observations=_observations(),
        candles_by_symbol=candles,
        setup_b_metrics=_setup_metrics(),
        iterations=10,
        seed=5403,
    )

    assert set(analysis["random_baseline"]["1r"]["expectancy_r"]) == {
        "mean",
        "median",
        "p10",
        "p25",
        "p75",
        "p90",
        "min",
        "max",
    }
    assert analysis["comparison"]["1r"]["random_baseline_inconclusive"] is True


def test_distribution_summary_percentiles() -> None:
    summary = _distribution_summary(
        [Decimal("0"), Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")]
    )

    assert summary["median"] == Decimal("2")
    assert summary["p25"] == Decimal("1.00")
    assert summary["p75"] == Decimal("3.00")


def test_no_http_network_imports() -> None:
    root = Path(__file__).parent.parent.parent
    paths = [
        root / "research" / "signal_observation" / "setup_b_random_baseline.py",
        root / "research" / "signal_observation" / "run_setup_b_random_baseline.py",
    ]
    forbidden_imports = {"urllib", "requests", "http.client", "socket"}

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert not forbidden_imports.intersection(imported_modules)
