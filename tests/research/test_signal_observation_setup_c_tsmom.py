from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import research.signal_observation.setup_c_tsmom as setup_c_tsmom
from research.signal_observation.candles import Candle
from research.signal_observation.setup_c_tsmom import (
    COST_BPS,
    RANDOM_ITERATIONS,
    RESULT_FAIL,
    RESULT_PARK,
    RESULT_PASS,
    TsmomInterval,
    build_tsmom_intervals,
    close_to_close_return,
    count_vol_proxy_skipped_intervals,
    cost_return,
    evaluate_c1_gate,
    format_tsmom_report,
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
    vol_proxy: str = "0.02",
) -> TsmomInterval:
    raw_return = Decimal(interval_return)
    signed_return = Decimal(direction) * raw_return
    vol = Decimal(vol_proxy)
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
    vt_discovery: str | None = None,
    vt_validation: str | None = None,
    vt_random_median: str | None = None,
    vt_random_p75: str | None = None,
    vt_symbol_values: tuple[str, str, str] | None = None,
    cost_ratio: str | None = "0.25",
    vt_cost_ratio: str | None = "0.25",
) -> dict[str, object]:
    vt_discovery = discovery if vt_discovery is None else vt_discovery
    vt_validation = validation if vt_validation is None else vt_validation
    vt_random_median = random_median if vt_random_median is None else vt_random_median
    vt_random_p75 = random_p75 if vt_random_p75 is None else vt_random_p75
    vt_symbol_values = symbol_values if vt_symbol_values is None else vt_symbol_values

    def metrics(value: str, vt_value: str) -> dict[str, object]:
        return {
            "post_cost_return": {"moderate": value},
            "volatility_targeted_post_cost_return": {"moderate": vt_value},
            "volatility_targeted_sharpe_like": vt_value,
            "cost_to_gross_ratio_moderate": cost_ratio,
            "volatility_targeted_cost_to_gross_ratio_moderate": vt_cost_ratio,
            "turnover": 0,
        }

    return {
        "metrics": {
            "full": metrics(discovery, vt_discovery),
            "discovery": metrics(discovery, vt_discovery),
            "validation": metrics(validation, vt_validation),
        },
        "per_symbol": {
            "full": {
                "BTCUSDT": metrics(symbol_values[0], vt_symbol_values[0]),
                "ETHUSDT": metrics(symbol_values[1], vt_symbol_values[1]),
                "SOLUSDT": metrics(symbol_values[2], vt_symbol_values[2]),
            }
        },
        "random_baseline": {
            "discovery": {
                "median": vt_random_median,
                "p75": vt_random_p75,
                "p90": vt_random_p75,
                "raw_return_diagnostics": {
                    "median": random_median,
                    "p75": random_p75,
                    "p90": random_p75,
                },
            }
        },
        "turnover_cost_diagnostics": {
            "BTCUSDT": {
                "full": {
                    "turnover": 0,
                    "volatility_targeted_cost_to_gross_ratio_moderate": vt_cost_ratio,
                    "raw_cost_to_gross_ratio_moderate": cost_ratio,
                },
                "vol_proxy_skipped_intervals": 0,
            },
            "ETHUSDT": {
                "full": {
                    "turnover": 0,
                    "volatility_targeted_cost_to_gross_ratio_moderate": vt_cost_ratio,
                    "raw_cost_to_gross_ratio_moderate": cost_ratio,
                },
                "vol_proxy_skipped_intervals": 0,
            },
            "SOLUSDT": {
                "full": {
                    "turnover": 0,
                    "volatility_targeted_cost_to_gross_ratio_moderate": vt_cost_ratio,
                    "raw_cost_to_gross_ratio_moderate": cost_ratio,
                },
                "vol_proxy_skipped_intervals": 0,
            },
        },
        "vol_proxy_skipped_intervals": {
            "total": 0,
            "by_symbol": {"BTCUSDT": 0, "ETHUSDT": 0, "SOLUSDT": 0},
            "downstream_policy": "invalid volatility rows are skipped before interval creation",
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


def test_random_baseline_summary_uses_volatility_targeted_metric() -> None:
    template = [
        _interval(
            symbol="BTCUSDT",
            timestamp="2026-01-01T00:00:00+00:00",
            interval_return="0",
            vol_proxy="0.02",
        )
    ]

    summary = random_baseline_summary(
        template,
        iterations=RANDOM_ITERATIONS,
        seed=5403,
    )

    assert summary["full"]["metric"] == "volatility_targeted_post_cost_return"
    assert summary["full"]["median"] == "-0.02"
    assert summary["full"]["raw_return_diagnostics"]["median"] == "-0.0004"


def test_skipped_invalid_vol_proxy_does_not_update_turnover_state(monkeypatch) -> None:
    candles = _candles(75, start="100", step="1")

    def proxy_or_skip(
        candles_arg: list[Candle],
        atr_values: list[Decimal | None],
        index: int,
    ) -> Decimal | None:
        if index == 60:
            return None
        return Decimal("0.02")

    monkeypatch.setattr(setup_c_tsmom, "_volatility_proxy_from_atr", proxy_or_skip)

    intervals = build_tsmom_intervals({"BTCUSDT": candles}, lookback=40)

    assert len(intervals) == 1
    assert intervals[0].timestamp == candles[66].timestamp.isoformat()
    assert intervals[0].direction == 1
    assert intervals[0].turnover_units == 1


def test_vol_proxy_skipped_intervals_are_documented(monkeypatch) -> None:
    candles = _candles(75, start="100", step="1")

    def proxy_or_skip(
        candles_arg: list[Candle],
        atr_values: list[Decimal | None],
        index: int,
    ) -> Decimal | None:
        if index == 60:
            return None
        return Decimal("0.02")

    monkeypatch.setattr(setup_c_tsmom, "_volatility_proxy_from_atr", proxy_or_skip)

    skipped = count_vol_proxy_skipped_intervals({"BTCUSDT": candles}, lookback=40)

    assert skipped["total"] == 1
    assert skipped["by_symbol"]["BTCUSDT"] == 1
    assert "skipped before interval creation" in skipped["downstream_policy"]


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

    assert (
        gate["gate_results"]["validation_volatility_targeted_post_cost_moderate_gte_0"]
        is False
    )
    assert gate["decision"] == RESULT_PARK


def test_c1_gate_uses_volatility_targeted_metrics_not_raw_metrics() -> None:
    primary = _lookback_result(
        discovery="0.50",
        validation="0.20",
        random_median="0.00",
        random_p75="0.10",
        symbol_values=("0.30", "0.20", "0.10"),
        vt_discovery="-0.01",
        vt_validation="0.10",
        vt_random_median="-0.02",
        vt_random_p75="-0.005",
        vt_symbol_values=("0.10", "0.10", "0.10"),
    )

    gate = evaluate_c1_gate(_gate_payload(primary))

    assert (
        gate["gate_results"]["discovery_volatility_targeted_post_cost_moderate_gt_0"]
        is False
    )
    assert gate["decision"] != "SETUP_C_TSMOM_PASS_CANDIDATE"


def test_c1_gate_random_baseline_comparison_uses_volatility_targeted_metrics() -> None:
    primary = _lookback_result(
        discovery="0.50",
        validation="0.20",
        random_median="0.00",
        random_p75="0.10",
        symbol_values=("0.30", "0.20", "0.10"),
        vt_discovery="0.50",
        vt_validation="0.20",
        vt_random_median="0.40",
        vt_random_p75="0.60",
        vt_symbol_values=("0.30", "0.20", "0.10"),
    )

    gate = evaluate_c1_gate(_gate_payload(primary))

    assert gate["gate_results"]["beats_random_median"] is True
    assert gate["gate_results"]["beats_random_p75"] is False
    assert gate["decision"] != RESULT_PASS


def test_c1_gate_symbol_count_uses_volatility_targeted_metrics() -> None:
    primary = _lookback_result(
        discovery="0.50",
        validation="0.20",
        random_median="0.00",
        random_p75="0.10",
        symbol_values=("0.30", "0.20", "0.10"),
        vt_discovery="0.50",
        vt_validation="0.20",
        vt_random_median="0.00",
        vt_random_p75="0.10",
        vt_symbol_values=("0.20", "-0.01", "-0.01"),
    )

    gate = evaluate_c1_gate(_gate_payload(primary))

    assert gate["gate_results"]["two_of_three_symbols_positive"] is False
    assert gate["decision"] == RESULT_FAIL


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


def test_report_headline_fields_are_volatility_targeted() -> None:
    primary = _lookback_result(
        discovery="0.50",
        validation="0.20",
        random_median="0.00",
        random_p75="0.10",
        symbol_values=("0.30", "0.20", "0.10"),
        vt_discovery="-0.01",
        vt_validation="0.10",
        vt_random_median="-0.02",
        vt_random_p75="-0.005",
        vt_symbol_values=("0.10", "0.10", "0.10"),
    )
    payload = _gate_payload(primary)
    report = {
        "gate": evaluate_c1_gate(payload),
        "primary_lookback": 40,
        "random_seed": 5403,
        "random_iterations": RANDOM_ITERATIONS,
        "lookbacks": {
            lookback: {
                "role": "primary" if lookback == "40" else "sensitivity",
                **result,
            }
            for lookback, result in payload.items()
        },
        "return_sign_autocorrelation_40": {
            "BTCUSDT": {
                "lag_1_sign_autocorrelation": "0",
                "near_zero": True,
                "observations": 10,
            }
        },
        "known_limitations": ["funding costs excluded"],
    }

    text = format_tsmom_report(report)

    assert "primary_metric: volatility_targeted_post_cost_return" in text
    assert "Fixed sensitivity table" in text
    assert "discovery_volatility_targeted_post_cost_moderate: -0.01" in text
    assert "raw_discovery_post_cost_moderate: 0.50" in text
    assert "40-bar return sign autocorrelation" in text


def test_summary_contains_expected_cost_fields() -> None:
    intervals = [
        _interval(symbol="BTCUSDT", turnover=1, interval_return="0.02"),
        _interval(symbol="ETHUSDT", turnover=2, interval_return="-0.01"),
    ]

    summary = summarize_intervals(intervals)

    assert summary["rebalance_observations"] == 2
    assert summary["turnover"] == 3
    assert summary["post_cost_return"]["moderate"] == "0.0088"
    assert summary["volatility_targeted_post_cost_return"]["moderate"] == "0.44"
    assert summary["volatility_targeted_sharpe_like"] is not None
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
