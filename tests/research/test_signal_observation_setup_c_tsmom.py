from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.setup_c_tsmom import (
    COST_BPS,
    RANDOM_ITERATIONS,
    RESULT_FAIL,
    RESULT_PARK,
    TsmomInterval,
    build_tsmom_intervals,
    close_to_close_return,
    cost_return,
    evaluate_c1_gate,
    random_baseline_summary,
    random_directions,
    rebalance_indices,
    summarize_intervals,
    tsmom_direction,
    turnover_units,
    volatility_proxy,
)


def _candle(index: int, close: str) -> Candle:
    value = Decimal(close)
    timestamp = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=4 * index)
    return Candle(
        timestamp=timestamp,
        open=value,
        high=value + Decimal("1"),
        low=value - Decimal("1"),
        close=value,
        volume=Decimal("100"),
    )


def _candles(count: int, *, start: str = "100", step: str = "1") -> list[Candle]:
    start_value = Decimal(start)
    step_value = Decimal(step)
    return [
        _candle(index, str(start_value + (step_value * Decimal(index))))
        for index in range(count)
    ]


def _interval(
    *,
    symbol: str = "BTCUSDT",
    timestamp: str = "2026-01-01T00:00:00+00:00",
    split: str = "discovery",
    direction: int = 1,
    turnover: int = 1,
    interval_return: str = "0.01",
) -> TsmomInterval:
    raw_return = Decimal(interval_return)
    signed_return = Decimal(direction) * raw_return
    vol = Decimal("0.02")
    post_cost = {
        scenario: signed_return - cost_return(turnover, bps)
        for scenario, bps in COST_BPS.items()
    }
    return TsmomInterval(
        symbol=symbol,
        timestamp=timestamp,
        split=split,
        lookback=40,
        direction=direction,
        turnover_units=turnover,
        interval_return=raw_return,
        gross_return=signed_return,
        normalized_return=signed_return / vol,
        post_cost_returns=post_cost,
        post_cost_normalized_returns={
            scenario: value / vol for scenario, value in post_cost.items()
        },
        vol_proxy=vol,
    )


def _lookback_result(
    *,
    discovery: str,
    validation: str,
    random_median: str,
    random_p75: str,
    symbol_values: tuple[str, str, str],
    cost_ratio: str | None = "0.25",
) -> dict[str, object]:
    def metrics(value: str) -> dict[str, object]:
        return {
            "post_cost_return": {"moderate": value},
            "cost_to_gross_ratio_moderate": cost_ratio,
        }

    return {
        "metrics": {
            "full": metrics(discovery),
            "discovery": metrics(discovery),
            "validation": metrics(validation),
        },
        "per_symbol": {
            "full": {
                "BTCUSDT": metrics(symbol_values[0]),
                "ETHUSDT": metrics(symbol_values[1]),
                "SOLUSDT": metrics(symbol_values[2]),
            }
        },
        "random_baseline": {
            "discovery": {
                "median": random_median,
                "p75": random_p75,
                "p90": random_p75,
            }
        },
    }


def _gate_payload(primary: dict[str, object]) -> dict[str, object]:
    return {
        "20": _lookback_result(
            discovery="0.00",
            validation="0.00",
            random_median="-0.01",
            random_p75="0.01",
            symbol_values=("0.00", "0.00", "0.00"),
        ),
        "40": primary,
        "60": _lookback_result(
            discovery="0.00",
            validation="0.00",
            random_median="-0.01",
            random_p75="0.01",
            symbol_values=("0.00", "0.00", "0.00"),
        ),
    }


def test_close_to_close_lookback_return_calculation() -> None:
    candles = [_candle(0, "100"), _candle(1, "105"), _candle(2, "110")]

    assert close_to_close_return(candles, 2, 2) == Decimal("0.1")


def test_insufficient_warmup_returns_no_signal() -> None:
    candles = [_candle(0, "100"), _candle(1, "105")]

    assert close_to_close_return(candles, 1, 2) is None
    assert tsmom_direction(None) == 0


def test_tsmom_direction_long_short_flat() -> None:
    assert tsmom_direction(Decimal("0.01")) == 1
    assert tsmom_direction(Decimal("-0.01")) == -1
    assert tsmom_direction(Decimal("0")) == 0


def test_rebalance_every_6_bars_after_shared_warmup() -> None:
    assert rebalance_indices(_candles(80)) == [60, 66, 72]


def test_atr20_close_volatility_proxy_handling() -> None:
    candles = _candles(25)

    assert volatility_proxy(candles, 18) is None
    proxy = volatility_proxy(candles, 20)
    assert proxy is not None
    assert proxy > Decimal("0")


def test_turnover_units_and_cost_calculation() -> None:
    assert turnover_units(0, 1) == 1
    assert turnover_units(1, 1) == 0
    assert turnover_units(1, -1) == 2
    assert cost_return(2, Decimal("4")) == Decimal("0.0008")


def test_build_intervals_uses_discovery_validation_split() -> None:
    data = {
        "BTCUSDT": _candles(90, start="100", step="1"),
        "ETHUSDT": _candles(90, start="110", step="1"),
        "SOLUSDT": _candles(90, start="120", step="1"),
    }

    intervals = build_tsmom_intervals(data, lookback=40)

    assert {item.split for item in intervals} == {"discovery", "validation"}
    assert all(item.lookback == 40 for item in intervals)


def test_random_baseline_uses_deterministic_seed_and_direction_domain() -> None:
    first = random_directions(12, seed=5403)
    second = random_directions(12, seed=5403)

    assert first == second
    assert set(first) <= {-1, 1}


def test_random_baseline_samples_per_rebalance_and_is_deterministic() -> None:
    template = [
        _interval(symbol="BTCUSDT", timestamp="2026-01-01T00:00:00+00:00"),
        _interval(symbol="ETHUSDT", timestamp="2026-01-01T00:00:00+00:00"),
        _interval(symbol="BTCUSDT", timestamp="2026-01-02T00:00:00+00:00"),
    ]

    first = random_baseline_summary(
        template,
        iterations=RANDOM_ITERATIONS,
        seed=5403,
    )
    second = random_baseline_summary(
        template,
        iterations=RANDOM_ITERATIONS,
        seed=5403,
    )

    assert first == second
    assert set(first) == {"full", "discovery", "validation"}


def test_c1_pass_gate_requires_2_of_3_positive_symbols() -> None:
    primary = _lookback_result(
        discovery="0.05",
        validation="0.01",
        random_median="0.00",
        random_p75="0.02",
        symbol_values=("0.03", "-0.01", "-0.02"),
    )

    gate = evaluate_c1_gate(_gate_payload(primary))

    assert gate["gate_results"]["two_of_three_symbols_positive"] is False
    assert gate["decision"] == RESULT_FAIL


def test_c1_cannot_pass_if_validation_post_cost_moderate_is_negative() -> None:
    primary = _lookback_result(
        discovery="0.05",
        validation="-0.01",
        random_median="0.00",
        random_p75="0.02",
        symbol_values=("0.03", "0.01", "-0.02"),
    )

    gate = evaluate_c1_gate(_gate_payload(primary))

    assert gate["gate_results"]["validation_post_cost_moderate_gte_0"] is False
    assert gate["decision"] == RESULT_PARK


def test_sensitivity_lookbacks_cannot_become_primary_pass() -> None:
    primary = _lookback_result(
        discovery="0.015",
        validation="0.01",
        random_median="0.00",
        random_p75="0.02",
        symbol_values=("0.03", "0.01", "-0.02"),
    )
    payload = _gate_payload(primary)
    payload["20"] = _lookback_result(
        discovery="0.10",
        validation="0.02",
        random_median="0.00",
        random_p75="0.02",
        symbol_values=("0.03", "0.02", "0.01"),
    )

    gate = evaluate_c1_gate(payload)

    assert gate["sensitivity_better_than_primary"] is True
    assert gate["decision"] == RESULT_PARK


def test_summary_contains_expected_cost_fields() -> None:
    intervals = [
        _interval(symbol="BTCUSDT", turnover=1, interval_return="0.02"),
        _interval(symbol="ETHUSDT", turnover=2, interval_return="-0.01"),
    ]

    summary = summarize_intervals(intervals)

    assert summary["rebalance_observations"] == 2
    assert summary["turnover"] == 3
    assert summary["post_cost_return"]["moderate"] == "0.0088"
    assert summary["cost_to_gross_ratio_moderate"] == "0.12"


def test_no_http_network_imports() -> None:
    root = Path(__file__).parent.parent.parent
    paths = [
        root / "research" / "signal_observation" / "setup_c_tsmom.py",
        root / "research" / "signal_observation" / "run_setup_c_tsmom.py",
    ]
    forbidden_imports = {
        "url" + "lib",
        "requ" + "ests",
        "http" + ".client",
        "sock" + "et",
    }

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert not forbidden_imports.intersection(imported_modules)
