"""Setup C TSMOM / volatility-targeted research evaluation."""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Sequence

from .candles import Candle
from .csv_loader import load_ohlcv_csv
from .indicators import atr


LOOKBACKS = (20, 40, 60)
PRIMARY_LOOKBACK = 40
ATR_PERIOD = 20
REBALANCE_BARS = 6
RANDOM_ITERATIONS = 1000
RANDOM_SEED = 5403
TINY_VOL_FLOOR = Decimal("0.000001")
COST_BPS = {
    "optimistic": Decimal("2"),
    "moderate": Decimal("4"),
    "conservative": Decimal("6"),
}
COST_SCENARIOS = tuple(COST_BPS)
PRIMARY_COST_SCENARIO = "moderate"
PRIMARY_GATE_METRIC = "volatility_targeted_post_cost_return"
FUNDING_RATES_PER_8H = {
    "favorable": Decimal("-0.0001"),
    "neutral": Decimal("0"),
    "mild_cost": Decimal("0.0001"),
    "high_cost": Decimal("0.0003"),
}
FUNDING_INTERVALS_PER_REBALANCE = (
    Decimal(REBALANCE_BARS) * Decimal("4") / Decimal("8")
)
RESULT_PASS = "SETUP_C_TSMOM_PASS_CANDIDATE"
RESULT_PARK = "SETUP_C_TSMOM_PARK"
RESULT_FAIL = "SETUP_C_TSMOM_FAIL"


@dataclass(frozen=True, slots=True)
class TsmomInterval:
    """One rebalance-to-rebalance research interval."""

    symbol: str
    timestamp: str
    split: str
    lookback: int
    direction: int
    turnover_units: int
    interval_return: Decimal
    gross_return: Decimal
    normalized_return: Decimal
    post_cost_returns: dict[str, Decimal]
    post_cost_normalized_returns: dict[str, Decimal]
    vol_proxy: Decimal


def close_to_close_return(
    candles: Sequence[Candle],
    index: int,
    lookback: int,
) -> Decimal | None:
    """Return close[t] / close[t-lookback] - 1 after warmup."""

    if lookback <= 0:
        raise ValueError("lookback must be positive")
    if index < lookback:
        return None
    previous_close = candles[index - lookback].close
    if previous_close <= Decimal("0"):
        return None
    return (candles[index].close / previous_close) - Decimal("1")


def tsmom_direction(lookback_return: Decimal | None) -> int:
    """Map lookback return to deterministic TSMOM direction."""

    if lookback_return is None:
        return 0
    if lookback_return > Decimal("0"):
        return 1
    if lookback_return < Decimal("0"):
        return -1
    return 0


def rebalance_indices(candles: Sequence[Candle], *, max_lookback: int = max(LOOKBACKS)) -> list[int]:
    """Return fixed 6-bar rebalance indices after shared warmup."""

    start = max(max_lookback, ATR_PERIOD - 1)
    return [index for index in range(start, len(candles) - REBALANCE_BARS, REBALANCE_BARS)]


def volatility_proxy(candles: Sequence[Candle], index: int) -> Decimal | None:
    """Return ATR(20) / close for one candle."""

    atr_values = atr(candles, period=ATR_PERIOD)
    return _volatility_proxy_from_atr(candles, atr_values, index)


def _volatility_proxy_from_atr(
    candles: Sequence[Candle],
    atr_values: Sequence[Decimal | None],
    index: int,
) -> Decimal | None:
    current_atr = atr_values[index]
    close = candles[index].close
    if current_atr is None or close <= Decimal("0"):
        return None
    proxy = current_atr / close
    if proxy <= Decimal("0"):
        return None
    return proxy


def turnover_units(previous_direction: int, current_direction: int) -> int:
    """Return turnover units for a direction transition."""

    if previous_direction == current_direction:
        return 0
    if previous_direction == 0 or current_direction == 0:
        return 1
    return 2


def cost_return(turnover: int, bps: Decimal) -> Decimal:
    """Convert bps-per-turnover to return units."""

    return Decimal(turnover) * bps / Decimal("10000")


def build_tsmom_intervals(
    candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    lookback: int,
) -> list[TsmomInterval]:
    """Build deterministic TSMOM research intervals for one lookback."""

    raw_rows: list[dict[str, object]] = []
    for symbol in sorted(candles_by_symbol):
        candles = list(candles_by_symbol[symbol])
        atr_values = atr(candles, period=ATR_PERIOD)
        previous_direction = 0
        for index in rebalance_indices(candles):
            next_index = index + REBALANCE_BARS
            lookback_value = close_to_close_return(candles, index, lookback)
            direction = tsmom_direction(lookback_value)
            proxy = _volatility_proxy_from_atr(candles, atr_values, index)
            if proxy is None:
                continue
            interval_return = (candles[next_index].close / candles[index].close) - Decimal("1")
            signed_return = Decimal(direction) * interval_return
            turnover = turnover_units(previous_direction, direction)
            previous_direction = direction
            vol = max(proxy, TINY_VOL_FLOOR)
            post_cost_returns = {
                scenario: signed_return - cost_return(turnover, bps)
                for scenario, bps in COST_BPS.items()
            }
            raw_rows.append(
                {
                    "symbol": symbol,
                    "timestamp": candles[index].timestamp.isoformat(),
                    "lookback": lookback,
                    "direction": direction,
                    "turnover_units": turnover,
                    "interval_return": interval_return,
                    "gross_return": signed_return,
                    "normalized_return": signed_return / vol,
                    "post_cost_returns": post_cost_returns,
                    "post_cost_normalized_returns": {
                        scenario: value / vol
                        for scenario, value in post_cost_returns.items()
                    },
                    "vol_proxy": vol,
                }
            )

    split_by_timestamp = _split_by_timestamp([str(item["timestamp"]) for item in raw_rows])
    intervals = [
        TsmomInterval(
            symbol=str(item["symbol"]),
            timestamp=str(item["timestamp"]),
            split=split_by_timestamp[str(item["timestamp"])],
            lookback=int(item["lookback"]),
            direction=int(item["direction"]),
            turnover_units=int(item["turnover_units"]),
            interval_return=item["interval_return"],  # type: ignore[arg-type]
            gross_return=item["gross_return"],  # type: ignore[arg-type]
            normalized_return=item["normalized_return"],  # type: ignore[arg-type]
            post_cost_returns=item["post_cost_returns"],  # type: ignore[arg-type]
            post_cost_normalized_returns=item["post_cost_normalized_returns"],  # type: ignore[arg-type]
            vol_proxy=item["vol_proxy"],  # type: ignore[arg-type]
        )
        for item in raw_rows
    ]
    return sorted(intervals, key=lambda item: (item.timestamp, item.symbol))


def count_vol_proxy_skipped_intervals(
    candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    lookback: int,
) -> dict[str, object]:
    """Count rebalance rows skipped because ATR/close volatility is invalid."""

    by_symbol: dict[str, int] = {}
    total = 0
    for symbol in sorted(candles_by_symbol):
        candles = list(candles_by_symbol[symbol])
        atr_values = atr(candles, period=ATR_PERIOD)
        skipped = 0
        for index in rebalance_indices(candles):
            if _volatility_proxy_from_atr(candles, atr_values, index) is None:
                skipped += 1
        by_symbol[symbol] = skipped
        total += skipped
    return {
        "total": total,
        "by_symbol": by_symbol,
        "downstream_policy": "invalid volatility rows are skipped before interval creation",
    }


def analyze_tsmom(
    candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    random_iterations: int = RANDOM_ITERATIONS,
    seed: int = RANDOM_SEED,
) -> dict[str, object]:
    """Analyze Setup C TSMOM across fixed lookbacks."""

    lookback_results: dict[str, object] = {}
    autocorrelation = {
        str(lookback): _sign_persistence(candles_by_symbol, lookback)
        for lookback in LOOKBACKS
    }
    return_sign_autocorrelation_40 = _return_sign_autocorrelation(
        candles_by_symbol,
        PRIMARY_LOOKBACK,
    )
    for lookback in LOOKBACKS:
        intervals = build_tsmom_intervals(candles_by_symbol, lookback=lookback)
        skipped = count_vol_proxy_skipped_intervals(
            candles_by_symbol,
            lookback=lookback,
        )
        random_summary = random_baseline_summary(
            intervals,
            iterations=random_iterations,
            seed=seed + lookback,
        )
        lookback_results[str(lookback)] = {
            "role": "primary" if lookback == PRIMARY_LOOKBACK else "sensitivity",
            "metrics": {
                "full": summarize_intervals(intervals),
                "discovery": summarize_intervals(
                    [item for item in intervals if item.split == "discovery"]
                ),
                "validation": summarize_intervals(
                    [item for item in intervals if item.split == "validation"]
                ),
            },
            "per_symbol": {
                split: _metrics_by_symbol(intervals, split)
                for split in ("full", "discovery", "validation")
            },
            "turnover_cost_diagnostics": _turnover_cost_diagnostics(
                intervals,
                skipped,
            ),
            "funding_stress": _funding_stress_diagnostics(intervals),
            "regime_decomposition": _regime_decomposition(intervals),
            "direction_change_frequency": _direction_change_frequency(intervals),
            "vol_proxy_skipped_intervals": skipped,
            "random_baseline": random_summary,
        }

    gate = evaluate_c1_gate(lookback_results)
    report = {
        "schema": "setup_c_tsmom_report_v1",
        "scope": "research_only_local_4h_ohlcv",
        "setup_family": "TSMOM / trend-following + volatility targeting",
        "primary_lookback": PRIMARY_LOOKBACK,
        "sensitivity_lookbacks": [20, 60],
        "rebalance_bars": REBALANCE_BARS,
        "volatility_proxy": "ATR(20) / close",
        "primary_metric": PRIMARY_GATE_METRIC,
        "raw_return_metrics_are_diagnostic_only": True,
        "random_seed": seed,
        "random_iterations": random_iterations,
        "cost_bps_per_turnover": _json_safe(COST_BPS),
        "funding_costs_excluded": True,
        "funding_stress_assumptions": {
            "diagnostic_only": True,
            "rates_per_8h": _json_safe(FUNDING_RATES_PER_8H),
            "funding_intervals_per_rebalance": FUNDING_INTERVALS_PER_REBALANCE,
            "applied_to": PRIMARY_GATE_METRIC,
        },
        "lookbacks": lookback_results,
        "autocorrelation_diagnostics": autocorrelation,
        "return_sign_autocorrelation_40": return_sign_autocorrelation_40,
        "autocorrelation_interpretation": [
            "high return-sign autocorrelation is expected for overlapping lookback windows",
            "return-sign autocorrelation does not by itself prove edge",
            "high autocorrelation indicates low independent information per bar",
            "interpretation should focus on rebalance intervals and direction-change frequency",
        ],
        "c4_regime_normalization": _primary_regime_normalization(lookback_results),
        "c5_regime_split": c5_regime_split_diagnostic(lookback_results),
        "c3_interpretation": _c3_interpretation(lookback_results, gate),
        "gate": gate,
        "known_limitations": [
            "funding costs excluded",
            "research-only normalized return calculation",
            "no execution or slippage model beyond bps turnover costs",
            "no sizing with capital",
            "no private API",
            "no paper or live readiness",
        ],
    }
    return _json_safe(report)  # type: ignore[return-value]


def summarize_intervals(intervals: Sequence[TsmomInterval]) -> dict[str, object]:
    """Summarize interval returns and turnover."""

    gross_returns = [item.gross_return for item in intervals]
    normalized_returns = [item.normalized_return for item in intervals]
    scenario_returns = {
        scenario: [item.post_cost_returns[scenario] for item in intervals]
        for scenario in COST_SCENARIOS
    }
    scenario_normalized_returns = {
        scenario: [item.post_cost_normalized_returns[scenario] for item in intervals]
        for scenario in COST_SCENARIOS
    }
    direction_counts = Counter(item.direction for item in intervals)
    turnover_total = sum(item.turnover_units for item in intervals)
    gross_total = sum(gross_returns, Decimal("0"))
    normalized_gross_total = sum(normalized_returns, Decimal("0"))
    moderate_cost_total = sum(
        cost_return(item.turnover_units, COST_BPS["moderate"])
        for item in intervals
    )
    moderate_normalized_cost_total = sum(
        cost_return(item.turnover_units, COST_BPS["moderate"]) / item.vol_proxy
        for item in intervals
    )
    return _json_safe(
        {
            "rebalance_observations": len(intervals),
            "direction_counts": {
                "long": direction_counts.get(1, 0),
                "short": direction_counts.get(-1, 0),
                "flat": direction_counts.get(0, 0),
            },
            "direction_changes": sum(1 for item in intervals if item.turnover_units > 0),
            "turnover": turnover_total,
            "gross_return": gross_total,
            "volatility_targeted_gross_return": normalized_gross_total,
            "post_cost_return": {
                scenario: sum(values, Decimal("0"))
                for scenario, values in scenario_returns.items()
            },
            "volatility_targeted_post_cost_return": {
                scenario: sum(values, Decimal("0"))
                for scenario, values in scenario_normalized_returns.items()
            },
            "average_interval_return": _average(gross_returns),
            "average_normalized_return": _average(normalized_returns),
            "average_post_cost_normalized_return": {
                scenario: _average(
                    [item.post_cost_normalized_returns[scenario] for item in intervals]
                )
                for scenario in COST_SCENARIOS
            },
            "sharpe_like": _sharpe_like(gross_returns),
            "volatility_targeted_sharpe_like": _sharpe_like(normalized_returns),
            "max_drawdown_like": _max_drawdown(gross_returns),
            "cost_to_gross_ratio_moderate": (
                moderate_cost_total / abs(gross_total)
                if gross_total != Decimal("0")
                else None
            ),
            "volatility_targeted_cost_to_gross_ratio_moderate": (
                moderate_normalized_cost_total / abs(normalized_gross_total)
                if normalized_gross_total != Decimal("0")
                else None
            ),
            "date_range": _date_range(intervals),
        }
    )


def random_baseline_summary(
    template_intervals: Sequence[TsmomInterval],
    *,
    iterations: int = RANDOM_ITERATIONS,
    seed: int = RANDOM_SEED,
) -> dict[str, object]:
    """Run matched random-direction baseline over existing rebalance bars."""

    if iterations < RANDOM_ITERATIONS:
        raise ValueError("random baseline requires at least 1000 iterations")

    split_values: dict[str, list[Decimal]] = {
        "full": [],
        "discovery": [],
        "validation": [],
    }
    raw_split_values: dict[str, list[Decimal]] = {
        "full": [],
        "discovery": [],
        "validation": [],
    }
    for iteration in range(iterations):
        rng = random.Random(seed + iteration)
        randomized = _randomized_intervals(template_intervals, rng)
        for split in ("full", "discovery", "validation"):
            if split == "full":
                scoped = randomized
            else:
                scoped = [item for item in randomized if item.split == split]
            split_values[split].append(
                _post_cost_normalized_total(scoped, PRIMARY_COST_SCENARIO)
            )
            raw_split_values[split].append(
                _post_cost_total(scoped, PRIMARY_COST_SCENARIO)
            )

    return _json_safe(
        {
            split: {
                "median": _median(values),
                "p75": _percentile(values, Decimal("0.75")),
                "p90": _percentile(values, Decimal("0.90")),
                "metric": PRIMARY_GATE_METRIC,
                "raw_return_diagnostics": {
                    "median": _median(raw_split_values[split]),
                    "p75": _percentile(raw_split_values[split], Decimal("0.75")),
                    "p90": _percentile(raw_split_values[split], Decimal("0.90")),
                },
            }
            for split, values in split_values.items()
        }
    )


def random_directions(
    count: int,
    *,
    seed: int,
) -> list[int]:
    """Return deterministic i.i.d. uniform random directions."""

    rng = random.Random(seed)
    return [rng.choice((-1, 1)) for _ in range(count)]


def evaluate_c1_gate(lookback_results: dict[str, object]) -> dict[str, object]:
    """Evaluate C1 gate only for the 40-bar primary design."""

    primary = lookback_results[str(PRIMARY_LOOKBACK)]  # type: ignore[index]
    metrics = primary["metrics"]  # type: ignore[index]
    random_summary = primary["random_baseline"]  # type: ignore[index]
    per_symbol_full = primary["per_symbol"]["full"]  # type: ignore[index]

    discovery = metrics["discovery"]  # type: ignore[index]
    validation = metrics["validation"]  # type: ignore[index]
    discovery_post_cost = _primary_gate_metric_value(discovery)
    validation_post_cost = _primary_gate_metric_value(validation)
    random_discovery = random_summary["discovery"]  # type: ignore[index]
    random_median = Decimal(str(random_discovery["median"]))
    random_p75 = Decimal(str(random_discovery["p75"]))
    positive_symbols = sum(
        1
        for symbol_metrics in per_symbol_full.values()
        if _primary_gate_metric_value(symbol_metrics) > Decimal("0")
    )
    cost_ratio_value = metrics["full"]["volatility_targeted_cost_to_gross_ratio_moderate"]  # type: ignore[index]
    costs_do_not_dominate = (
        cost_ratio_value is not None
        and Decimal(str(cost_ratio_value)) <= Decimal("0.50")
    )
    gate_results = {
        "discovery_volatility_targeted_post_cost_moderate_gt_0": discovery_post_cost > Decimal("0"),
        "beats_random_median": discovery_post_cost > random_median,
        "beats_random_p75": discovery_post_cost > random_p75,
        "two_of_three_symbols_positive": positive_symbols >= 2,
        "costs_do_not_dominate_volatility_targeted_gross": costs_do_not_dominate,
        "validation_volatility_targeted_post_cost_moderate_gte_0": validation_post_cost >= Decimal("0"),
    }

    sensitivity_better_than_primary = _sensitivity_better_than_primary(lookback_results)
    sensitivity_robustness = _sensitivity_robustness_diagnostics(lookback_results)
    passes = (
        gate_results["discovery_volatility_targeted_post_cost_moderate_gt_0"]
        and gate_results["beats_random_p75"]
        and gate_results["two_of_three_symbols_positive"]
        and gate_results["costs_do_not_dominate_volatility_targeted_gross"]
        and gate_results["validation_volatility_targeted_post_cost_moderate_gte_0"]
    )
    if passes:
        decision = RESULT_PASS
    elif (
        not gate_results["discovery_volatility_targeted_post_cost_moderate_gt_0"]
        or not gate_results["beats_random_median"]
        or not gate_results["two_of_three_symbols_positive"]
        or not gate_results["costs_do_not_dominate_volatility_targeted_gross"]
    ):
        decision = RESULT_FAIL
    else:
        decision = RESULT_PARK

    if decision == RESULT_FAIL and sensitivity_better_than_primary:
        decision = RESULT_PARK

    return _json_safe(
        {
            "decision": decision,
            "primary_lookback_only": True,
            "primary_metric": PRIMARY_GATE_METRIC,
            "gate_results": gate_results,
            "positive_symbol_count": positive_symbols,
            "sensitivity_better_than_primary": sensitivity_better_than_primary,
            "sensitivity_robustness": sensitivity_robustness,
            "notes": [
                "PASS is research-only and not paper-ready",
                "funding costs excluded",
                "moderate cost is the primary gate",
            ],
        }
    )


def c5_regime_split_diagnostic(lookback_results: dict[str, object]) -> dict[str, object]:
    """C5: report high_vol/low_vol regime metrics by discovery and validation split."""

    primary = lookback_results[str(PRIMARY_LOOKBACK)]  # type: ignore[index]
    regime = primary["regime_decomposition"]  # type: ignore[index]
    disc_high = _regime_normalization_bucket(regime["discovery"]["high_vol"])  # type: ignore[index]
    disc_low = _regime_normalization_bucket(regime["discovery"]["low_vol"])  # type: ignore[index]
    val_high = _regime_normalization_bucket(regime["validation"]["high_vol"])  # type: ignore[index]
    val_low = _regime_normalization_bucket(regime["validation"]["low_vol"])  # type: ignore[index]
    interpretation_result, interpretation = _c5_interpretation(disc_high, disc_low, val_high, val_low)
    return _json_safe(
        {
            "lookback": PRIMARY_LOOKBACK,
            "diagnostic_only": True,
            "candidate_inclusion_unchanged": True,
            "strategy_filter_introduced": False,
            "primary_gate_unchanged": True,
            "bucket_source": "same high_vol/low_vol definitions as C3 regime_decomposition per split",
            "discovery": {
                "high_vol": disc_high,
                "low_vol": disc_low,
            },
            "validation": {
                "high_vol": val_high,
                "low_vol": val_low,
            },
            "interpretation_result": interpretation_result,
            "interpretation": interpretation,
        }
    )  # type: ignore[return-value]


def load_bitget_4h_candles(data_dir: str | Path) -> dict[str, list[Candle]]:
    """Load fixed local Bitget 4H CSVs for Setup C."""

    base = Path(data_dir)
    symbols = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    return {
        symbol: load_ohlcv_csv(base / f"{symbol}_USDT-FUTURES_4H.csv")
        for symbol in symbols
    }


def write_tsmom_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic text and JSON artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_tsmom_report(report), encoding="utf-8")
    json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_tsmom_report(report: dict[str, object]) -> str:
    """Format a concise deterministic Setup C report."""

    lines = [
        "Setup C TSMOM / volatility targeting report",
        "",
        "Scope: research-only local 4H OHLCV evaluation.",
        "No detector/runtime/private API/paper/live readiness claim.",
        "",
        f"decision: {report['gate']['decision']}",  # type: ignore[index]
        f"primary_lookback: {report['primary_lookback']}",
        f"random_seed: {report['random_seed']}",
        f"random_iterations: {report['random_iterations']}",
        "funding_costs_excluded: True",
        f"primary_metric: {PRIMARY_GATE_METRIC}",
        "raw_return_metrics: diagnostic_only",
        "",
        "Lookback summaries",
    ]
    lookbacks = report["lookbacks"]  # type: ignore[assignment]
    lines.extend(
        [
            "Fixed sensitivity table",
            "lookback | role | vt_sharpe | vt_post_cost_moderate_full | turnover | vt_cost_to_gross",
        ]
    )
    for lookback in ("20", "40", "60"):
        item = lookbacks[lookback]
        full = item["metrics"]["full"]
        lines.append(
            f"{lookback} | {item['role']} | "
            f"{full['volatility_targeted_sharpe_like']} | "
            f"{full['volatility_targeted_post_cost_return'][PRIMARY_COST_SCENARIO]} | "
            f"{full['turnover']} | "
            f"{full['volatility_targeted_cost_to_gross_ratio_moderate']}"
        )
    lines.append("")
    for lookback in ("20", "40", "60"):
        item = lookbacks[lookback]
        role = item["role"]
        metrics = item["metrics"]
        random_summary = item["random_baseline"]["discovery"]
        discovery = metrics["discovery"]
        validation = metrics["validation"]
        full = metrics["full"]
        lines.extend(
            [
                f"lookback: {lookback} ({role})",
                "  discovery_volatility_targeted_post_cost_moderate: "
                f"{discovery['volatility_targeted_post_cost_return']['moderate']}",
                "  validation_volatility_targeted_post_cost_moderate: "
                f"{validation['volatility_targeted_post_cost_return']['moderate']}",
                "  full_volatility_targeted_post_cost_moderate: "
                f"{full['volatility_targeted_post_cost_return']['moderate']}",
                f"  discovery_volatility_targeted_random_median/p75/p90: "
                f"{random_summary['median']} / {random_summary['p75']} / {random_summary['p90']}",
                f"  raw_discovery_post_cost_moderate: {discovery['post_cost_return']['moderate']}",
                f"  raw_validation_post_cost_moderate: {validation['post_cost_return']['moderate']}",
                f"  raw_full_post_cost_moderate: {full['post_cost_return']['moderate']}",
                f"  turnover: {full['turnover']}",
                "  volatility_targeted_cost_to_gross_ratio_moderate: "
                f"{full['volatility_targeted_cost_to_gross_ratio_moderate']}",
                f"  raw_cost_to_gross_ratio_moderate: {full['cost_to_gross_ratio_moderate']}",
            ]
        )
        skipped = item["vol_proxy_skipped_intervals"]
        lines.append(f"  vol_proxy_skipped_intervals_total: {skipped['total']}")
        lines.append("  per_symbol_full_volatility_targeted_post_cost_moderate:")
        for symbol, symbol_metrics in sorted(item["per_symbol"]["full"].items()):
            lines.append(
                f"    {symbol}: "
                f"{symbol_metrics['volatility_targeted_post_cost_return']['moderate']}"
            )
        lines.append("  turnover_cost_diagnostics_full_by_symbol:")
        for symbol, symbol_metrics in sorted(item["turnover_cost_diagnostics"].items()):
            full_breakdown = symbol_metrics["full"]
            lines.append(
                f"    {symbol}: turnover={full_breakdown['turnover']}; "
                f"vt_cost_to_gross={full_breakdown['volatility_targeted_cost_to_gross_ratio_moderate']}; "
                f"raw_cost_to_gross={full_breakdown['raw_cost_to_gross_ratio_moderate']}; "
                f"skipped={symbol_metrics['vol_proxy_skipped_intervals']}"
            )
        lines.append("  funding_stress_full:")
        for scenario, values in sorted(item["funding_stress"]["full"].items()):
            lines.append(
                f"    {scenario}: impact={values['funding_impact_on_vt_post_cost_return']}; "
                f"adjusted={values['funding_adjusted_vt_post_cost_return']}"
            )
        lines.append("  regime_decomposition_full:")
        for regime, values in sorted(item["regime_decomposition"]["full"].items()):
            if regime == "policy":
                continue
            lines.append(
                f"    {regime}: count={values['rebalance_observations']}; "
                f"vt_gross={values['volatility_targeted_gross_return']}; "
                f"vt_post_cost_moderate={values['volatility_targeted_post_cost_return']['moderate']}; "
                f"turnover={values['turnover']}; "
                f"vt_cost_to_gross={values['volatility_targeted_cost_to_gross_ratio_moderate']}"
            )
        direction_frequency = item["direction_change_frequency"]["full"]
        lines.append(
            "  direction_change_frequency_full_pooled: "
            f"observations={direction_frequency['pooled']['rebalance_observations']}; "
            f"changes={direction_frequency['pooled']['direction_changes']}; "
            f"pct={direction_frequency['pooled']['direction_change_pct']}"
        )

    lines.extend(["", "40-bar return sign autocorrelation"])
    for note in report["autocorrelation_interpretation"]:  # type: ignore[index]
        lines.append(f"  interpretation: {note}")
    autocorrelation_40 = report["return_sign_autocorrelation_40"]  # type: ignore[assignment]
    for symbol, values in sorted(autocorrelation_40.items()):
        lines.append(
            f"  {symbol}: lag_1={values['lag_1_sign_autocorrelation']}; "
            f"near_zero={values['near_zero']}; observations={values['observations']}"
        )

    lines.extend(["", "Primary gate"])
    gate = report["gate"]  # type: ignore[assignment]
    for key, value in gate["gate_results"].items():
        lines.append(f"  {key}: {value}")
    lines.append("  sensitivity_robustness:")
    for lookback, values in sorted(gate["sensitivity_robustness"].items()):
        lines.append(
            f"    {lookback}: discovery_better_than_primary={values['discovery_better_than_primary']}; "
            f"validation_non_negative={values['validation_non_negative']}; "
            f"robust_sensitivity_candidate={values['robust_sensitivity_candidate']}"
        )

    lines.extend(["", "C3 interpretation"])
    for item in report["c3_interpretation"]:  # type: ignore[index]
        lines.append(f"- {item}")

    c4 = report["c4_regime_normalization"]  # type: ignore[index]
    lines.extend(["", "C4 regime normalization diagnostic"])
    lines.append("  policy: observational_only; no_filter; no_gate_change")
    for bucket in ("high_vol", "low_vol"):
        values = c4["buckets"][bucket]
        lines.append(
            f"  {bucket}: count={values['count']}; "
            f"raw_gross={values['raw_gross_return']}; "
            f"raw_post_cost_moderate={values['raw_post_cost_moderate']}; "
            f"turnover={values['turnover']}; "
            f"raw_cost_to_gross={values['raw_cost_to_gross_ratio_moderate']}; "
            f"vt_post_cost_moderate={values['volatility_targeted_post_cost_moderate']}"
        )
    lines.append(f"  interpretation_result: {c4['interpretation_result']}")
    lines.append(f"  interpretation: {c4['interpretation']}")

    c5 = report["c5_regime_split"]  # type: ignore[index]
    lines.extend(["", "C5 regime split diagnostic"])
    lines.append("  policy: observational_only; no_filter; no_gate_change")
    for split in ("discovery", "validation"):
        for bucket in ("high_vol", "low_vol"):
            values = c5[split][bucket]  # type: ignore[index]
            lines.append(
                f"  {split}_{bucket}: count={values['count']}; "  # type: ignore[index]
                f"raw_gross={values['raw_gross_return']}; "  # type: ignore[index]
                f"raw_post_cost_moderate={values['raw_post_cost_moderate']}; "  # type: ignore[index]
                f"vt_gross={values['volatility_targeted_gross_return']}; "  # type: ignore[index]
                f"vt_post_cost_moderate={values['volatility_targeted_post_cost_moderate']}; "  # type: ignore[index]
                f"turnover={values['turnover']}; "  # type: ignore[index]
                f"raw_cost_to_gross={values['raw_cost_to_gross_ratio_moderate']}; "  # type: ignore[index]
                f"vt_cost_to_gross={values['volatility_targeted_cost_to_gross_ratio_moderate']}"  # type: ignore[index]
            )
    lines.append(f"  interpretation_result: {c5['interpretation_result']}")  # type: ignore[index]
    lines.append(f"  interpretation: {c5['interpretation']}")  # type: ignore[index]

    lines.extend(["", "Known limitations"])
    for limitation in report["known_limitations"]:  # type: ignore[index]
        lines.append(f"- {limitation}")
    return "\n".join(lines).rstrip() + "\n"


def _randomized_intervals(
    template_intervals: Sequence[TsmomInterval],
    rng: random.Random,
) -> list[TsmomInterval]:
    previous_by_symbol: dict[str, int] = defaultdict(int)
    randomized: list[TsmomInterval] = []
    for item in sorted(template_intervals, key=lambda value: (value.timestamp, value.symbol)):
        direction = rng.choice((-1, 1))
        turnover = turnover_units(previous_by_symbol[item.symbol], direction)
        previous_by_symbol[item.symbol] = direction
        signed_return = Decimal(direction) * item.interval_return
        post_cost = {
            scenario: signed_return - cost_return(turnover, bps)
            for scenario, bps in COST_BPS.items()
        }
        randomized.append(
            TsmomInterval(
                symbol=item.symbol,
                timestamp=item.timestamp,
                split=item.split,
                lookback=item.lookback,
                direction=direction,
                turnover_units=turnover,
                interval_return=item.interval_return,
                gross_return=signed_return,
                normalized_return=signed_return / item.vol_proxy,
                post_cost_returns=post_cost,
                post_cost_normalized_returns={
                    scenario: value / item.vol_proxy for scenario, value in post_cost.items()
                },
                vol_proxy=item.vol_proxy,
            )
        )
    return randomized


def _metrics_by_symbol(
    intervals: Sequence[TsmomInterval],
    split: str,
) -> dict[str, object]:
    if split == "full":
        scoped = list(intervals)
    else:
        scoped = [item for item in intervals if item.split == split]
    groups: dict[str, list[TsmomInterval]] = defaultdict(list)
    for item in scoped:
        groups[item.symbol].append(item)
    return {
        symbol: summarize_intervals(groups[symbol])
        for symbol in sorted(groups)
    }


def _turnover_cost_diagnostics(
    intervals: Sequence[TsmomInterval],
    skipped: dict[str, object],
) -> dict[str, object]:
    groups: dict[str, list[TsmomInterval]] = defaultdict(list)
    for item in intervals:
        groups[item.symbol].append(item)

    output: dict[str, object] = {}
    skipped_by_symbol = skipped.get("by_symbol", {})
    for symbol in sorted(groups):
        symbol_output: dict[str, object] = {}
        for split in ("full", "discovery", "validation"):
            if split == "full":
                scoped = groups[symbol]
            else:
                scoped = [item for item in groups[symbol] if item.split == split]
            summary = summarize_intervals(scoped)
            symbol_output[split] = {
                "rebalance_observations": summary["rebalance_observations"],
                "turnover": summary["turnover"],
                "raw_gross_return": summary["gross_return"],
                "raw_post_cost_moderate": summary["post_cost_return"][PRIMARY_COST_SCENARIO],  # type: ignore[index]
                "volatility_targeted_gross_return": summary["volatility_targeted_gross_return"],
                "volatility_targeted_post_cost_moderate": summary["volatility_targeted_post_cost_return"][PRIMARY_COST_SCENARIO],  # type: ignore[index]
                "raw_cost_to_gross_ratio_moderate": summary["cost_to_gross_ratio_moderate"],
                "volatility_targeted_cost_to_gross_ratio_moderate": summary["volatility_targeted_cost_to_gross_ratio_moderate"],
            }
        symbol_output["vol_proxy_skipped_intervals"] = (
            skipped_by_symbol.get(symbol, 0)
            if isinstance(skipped_by_symbol, dict)
            else 0
        )
        output[symbol] = symbol_output
    return output


def _funding_stress_diagnostics(
    intervals: Sequence[TsmomInterval],
) -> dict[str, object]:
    return _json_safe({
        split: _funding_stress_for_split(
            intervals if split == "full" else [item for item in intervals if item.split == split]
        )
        for split in ("full", "discovery", "validation")
    })  # type: ignore[return-value]


def _funding_stress_for_split(
    intervals: Sequence[TsmomInterval],
) -> dict[str, object]:
    baseline = _post_cost_normalized_total(intervals, PRIMARY_COST_SCENARIO)
    output: dict[str, object] = {}
    for scenario, funding_rate in FUNDING_RATES_PER_8H.items():
        impact = sum(
            (_funding_impact_normalized(item, funding_rate) for item in intervals),
            Decimal("0"),
        )
        output[scenario] = {
            "funding_rate_per_8h": funding_rate,
            "funding_intervals_per_rebalance": FUNDING_INTERVALS_PER_REBALANCE,
            "baseline_vt_post_cost_return": baseline,
            "funding_impact_on_vt_post_cost_return": impact,
            "funding_adjusted_vt_post_cost_return": baseline + impact,
            "diagnostic_only": True,
        }
    return output


def _funding_impact_normalized(
    interval: TsmomInterval,
    funding_rate: Decimal,
) -> Decimal:
    if interval.direction == 0:
        return Decimal("0")
    raw_impact = (
        Decimal(-interval.direction)
        * funding_rate
        * FUNDING_INTERVALS_PER_REBALANCE
    )
    return raw_impact / interval.vol_proxy


def _regime_decomposition(intervals: Sequence[TsmomInterval]) -> dict[str, object]:
    return _json_safe({
        split: _regime_decomposition_for_split(
            intervals if split == "full" else [item for item in intervals if item.split == split]
        )
        for split in ("full", "discovery", "validation")
    })  # type: ignore[return-value]


def _regime_decomposition_for_split(
    intervals: Sequence[TsmomInterval],
) -> dict[str, object]:
    scoped = sorted(intervals, key=lambda item: (item.timestamp, item.symbol))
    threshold = _median([item.vol_proxy for item in scoped])
    high_low_groups = {
        "high_vol": [],
        "low_vol": [],
    }
    expanding_groups = {
        "volatility_expanding": [],
        "volatility_contracting": [],
    }

    previous_vol_by_symbol: dict[str, Decimal] = {}
    for item in scoped:
        if threshold is not None and item.vol_proxy >= threshold:
            high_low_groups["high_vol"].append(item)
        else:
            high_low_groups["low_vol"].append(item)

        previous_vol = previous_vol_by_symbol.get(item.symbol)
        if previous_vol is not None and item.vol_proxy > previous_vol:
            expanding_groups["volatility_expanding"].append(item)
        else:
            expanding_groups["volatility_contracting"].append(item)
        previous_vol_by_symbol[item.symbol] = item.vol_proxy

    output = {
        regime: summarize_intervals(values)
        for regime, values in {**high_low_groups, **expanding_groups}.items()
    }
    output["policy"] = {
        "diagnostic_only": True,
        "candidate_inclusion_unchanged": True,
        "high_low_threshold": threshold,
        "high_low_rule": "high_vol if interval ATR/close proxy is greater than or equal to split median",
        "expansion_rule": "volatility_expanding if current interval ATR/close proxy is greater than previous same-symbol rebalance proxy",
        "first_interval_policy": "first interval per symbol is counted as volatility_contracting for deterministic coverage",
    }
    return output


def _direction_change_frequency(
    intervals: Sequence[TsmomInterval],
) -> dict[str, object]:
    return _json_safe({
        split: _direction_change_frequency_for_split(
            intervals if split == "full" else [item for item in intervals if item.split == split]
        )
        for split in ("full", "discovery", "validation")
    })  # type: ignore[return-value]


def _direction_change_frequency_for_split(
    intervals: Sequence[TsmomInterval],
) -> dict[str, object]:
    groups: dict[str, list[TsmomInterval]] = defaultdict(list)
    for item in intervals:
        groups[item.symbol].append(item)
    output: dict[str, object] = {
        symbol: _direction_frequency_summary(groups[symbol])
        for symbol in sorted(groups)
    }
    output["pooled"] = _direction_frequency_summary(list(intervals))
    return output


def _direction_frequency_summary(
    intervals: Sequence[TsmomInterval],
) -> dict[str, object]:
    observations = len(intervals)
    changes = sum(1 for item in intervals if item.turnover_units > 0)
    return {
        "rebalance_observations": observations,
        "direction_changes": changes,
        "direction_change_pct": (
            Decimal(changes) / Decimal(observations)
            if observations
            else None
        ),
    }


def _split_by_timestamp(timestamps: Sequence[str]) -> dict[str, str]:
    unique = sorted(set(timestamps))
    if not unique:
        return {}
    cutoff_index = int((Decimal(len(unique)) * Decimal("0.70")).to_integral_value(rounding="ROUND_FLOOR"))
    cutoff_index = min(max(cutoff_index, 1), len(unique)) - 1
    cutoff = unique[cutoff_index]
    return {
        timestamp: "discovery" if timestamp <= cutoff else "validation"
        for timestamp in unique
    }


def _post_cost_total(intervals: Sequence[TsmomInterval], scenario: str) -> Decimal:
    return sum((item.post_cost_returns[scenario] for item in intervals), Decimal("0"))


def _post_cost_normalized_total(intervals: Sequence[TsmomInterval], scenario: str) -> Decimal:
    return sum(
        (item.post_cost_normalized_returns[scenario] for item in intervals),
        Decimal("0"),
    )


def _primary_gate_metric_value(metrics: dict[str, object]) -> Decimal:
    value = metrics[PRIMARY_GATE_METRIC][PRIMARY_COST_SCENARIO]  # type: ignore[index]
    return Decimal(str(value))


def _average(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, Decimal("0")) / Decimal(len(values))


def _median(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / Decimal("2")


def _percentile(values: Sequence[Decimal], percentile: Decimal) -> Decimal | None:
    if not values:
        return None
    sorted_values = sorted(values)
    index = int((Decimal(len(sorted_values) - 1) * percentile).to_integral_value(rounding="ROUND_FLOOR"))
    return sorted_values[index]


def _sharpe_like(values: Sequence[Decimal]) -> Decimal | None:
    if len(values) < 2:
        return None
    average = _average(values)
    if average is None:
        return None
    variance = sum(((value - average) * (value - average) for value in values), Decimal("0")) / Decimal(len(values) - 1)
    if variance <= Decimal("0"):
        return None
    return average / variance.sqrt()


def _max_drawdown(values: Sequence[Decimal]) -> Decimal:
    equity = Decimal("0")
    peak = Decimal("0")
    drawdown = Decimal("0")
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def _date_range(intervals: Sequence[TsmomInterval]) -> dict[str, str | None]:
    if not intervals:
        return {"first": None, "last": None}
    timestamps = sorted(item.timestamp for item in intervals)
    return {"first": timestamps[0], "last": timestamps[-1]}


def _sign_persistence(
    candles_by_symbol: dict[str, Sequence[Candle]],
    lookback: int,
) -> dict[str, object]:
    output: dict[str, object] = {}
    total_matches = 0
    total_count = 0
    for symbol in sorted(candles_by_symbol):
        candles = candles_by_symbol[symbol]
        returns = [
            (candles[index].close / candles[index - 1].close) - Decimal("1")
            for index in range(1, len(candles))
            if candles[index - 1].close > Decimal("0")
        ]
        matches = 0
        count = 0
        for index in range(lookback, len(returns)):
            current = _sign(returns[index])
            previous = _sign(returns[index - lookback])
            if current == 0 or previous == 0:
                continue
            count += 1
            if current == previous:
                matches += 1
        total_matches += matches
        total_count += count
        output[symbol] = {
            "observations": count,
            "same_sign_rate": str(Decimal(matches) / Decimal(count)) if count else None,
        }
    output["pooled"] = {
        "observations": total_count,
        "same_sign_rate": (
            str(Decimal(total_matches) / Decimal(total_count))
            if total_count
            else None
        ),
    }
    return output


def _return_sign_autocorrelation(
    candles_by_symbol: dict[str, Sequence[Candle]],
    lookback: int,
) -> dict[str, object]:
    output: dict[str, object] = {}
    pooled_signs: list[int] = []
    for symbol in sorted(candles_by_symbol):
        signs = _lookback_return_signs(candles_by_symbol[symbol], lookback)
        pooled_signs.extend(signs)
        autocorrelation = _lag_one_correlation(signs)
        output[symbol] = {
            "lookback": lookback,
            "observations": max(len(signs) - 1, 0),
            "lag_1_sign_autocorrelation": autocorrelation,
            "near_zero": _near_zero_autocorrelation(autocorrelation),
        }

    pooled_autocorrelation = _lag_one_correlation(pooled_signs)
    output["pooled"] = {
        "lookback": lookback,
        "observations": max(len(pooled_signs) - 1, 0),
        "lag_1_sign_autocorrelation": pooled_autocorrelation,
        "near_zero": _near_zero_autocorrelation(pooled_autocorrelation),
    }
    return _json_safe(output)  # type: ignore[return-value]


def _lookback_return_signs(candles: Sequence[Candle], lookback: int) -> list[int]:
    signs: list[int] = []
    for index in range(lookback, len(candles)):
        value = close_to_close_return(candles, index, lookback)
        sign = tsmom_direction(value)
        if sign != 0:
            signs.append(sign)
    return signs


def _lag_one_correlation(signs: Sequence[int]) -> Decimal | None:
    if len(signs) < 3:
        return None
    x_values = [Decimal(value) for value in signs[:-1]]
    y_values = [Decimal(value) for value in signs[1:]]
    x_mean = _average(x_values)
    y_mean = _average(y_values)
    if x_mean is None or y_mean is None:
        return None
    covariance = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x_values, y_values, strict=True)
    )
    x_variance = sum((x_value - x_mean) * (x_value - x_mean) for x_value in x_values)
    y_variance = sum((y_value - y_mean) * (y_value - y_mean) for y_value in y_values)
    if x_variance <= Decimal("0") or y_variance <= Decimal("0"):
        return None
    return covariance / (x_variance * y_variance).sqrt()


def _near_zero_autocorrelation(value: Decimal | str | None) -> bool:
    if value is None:
        return False
    return abs(Decimal(str(value))) <= Decimal("0.05")


def _sign(value: Decimal) -> int:
    if value > Decimal("0"):
        return 1
    if value < Decimal("0"):
        return -1
    return 0


def _sensitivity_better_than_primary(lookback_results: dict[str, object]) -> bool:
    primary = lookback_results[str(PRIMARY_LOOKBACK)]  # type: ignore[index]
    primary_value = _primary_gate_metric_value(primary["metrics"]["discovery"])  # type: ignore[index]
    for lookback in ("20", "60"):
        value = _primary_gate_metric_value(
            lookback_results[lookback]["metrics"]["discovery"]  # type: ignore[index]
        )
        if value > primary_value:
            return True
    return False


def _sensitivity_robustness_diagnostics(
    lookback_results: dict[str, object],
) -> dict[str, object]:
    primary = lookback_results[str(PRIMARY_LOOKBACK)]  # type: ignore[index]
    primary_discovery = _primary_gate_metric_value(primary["metrics"]["discovery"])  # type: ignore[index]
    output: dict[str, object] = {}
    for lookback in ("20", "60"):
        result = lookback_results[lookback]  # type: ignore[index]
        discovery = _primary_gate_metric_value(result["metrics"]["discovery"])  # type: ignore[index]
        validation = _primary_gate_metric_value(result["metrics"]["validation"])  # type: ignore[index]
        discovery_better = discovery > primary_discovery
        validation_non_negative = validation >= Decimal("0")
        output[lookback] = {
            "discovery_better_than_primary": discovery_better,
            "validation_non_negative": validation_non_negative,
            "robust_sensitivity_candidate": discovery_better and validation_non_negative,
            "diagnostic_only": True,
            "interpretation": "sensitivity strength is not robust unless validation is non-negative",
        }
    return output


def _primary_regime_normalization(
    lookback_results: dict[str, object],
) -> dict[str, object]:
    primary = lookback_results[str(PRIMARY_LOOKBACK)]  # type: ignore[index]
    regime = primary["regime_decomposition"]["full"]  # type: ignore[index]
    high_vol = _regime_normalization_bucket(regime["high_vol"])
    low_vol = _regime_normalization_bucket(regime["low_vol"])
    interpretation_result, interpretation = _regime_normalization_interpretation(
        high_vol,
        low_vol,
    )
    return _json_safe(
        {
            "lookback": PRIMARY_LOOKBACK,
            "diagnostic_only": True,
            "candidate_inclusion_unchanged": True,
            "strategy_filter_introduced": False,
            "primary_gate_unchanged": True,
            "bucket_source": "same high_vol/low_vol definitions as C3 regime_decomposition",
            "buckets": {
                "high_vol": high_vol,
                "low_vol": low_vol,
            },
            "comparison": {
                "raw_high_vol_post_cost_moderate": high_vol["raw_post_cost_moderate"],
                "raw_low_vol_post_cost_moderate": low_vol["raw_post_cost_moderate"],
                "vt_high_vol_post_cost_moderate": high_vol["volatility_targeted_post_cost_moderate"],
                "vt_low_vol_post_cost_moderate": low_vol["volatility_targeted_post_cost_moderate"],
            },
            "interpretation_result": interpretation_result,
            "interpretation": interpretation,
        }
    )  # type: ignore[return-value]


def _regime_normalization_bucket(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "count": metrics["rebalance_observations"],
        "raw_gross_return": metrics["gross_return"],
        "raw_post_cost_moderate": metrics["post_cost_return"][PRIMARY_COST_SCENARIO],  # type: ignore[index]
        "turnover": metrics["turnover"],
        "raw_cost_to_gross_ratio_moderate": metrics["cost_to_gross_ratio_moderate"],
        "volatility_targeted_gross_return": metrics["volatility_targeted_gross_return"],
        "volatility_targeted_post_cost_moderate": metrics["volatility_targeted_post_cost_return"][PRIMARY_COST_SCENARIO],  # type: ignore[index]
        "volatility_targeted_cost_to_gross_ratio_moderate": metrics["volatility_targeted_cost_to_gross_ratio_moderate"],
    }


def _regime_normalization_interpretation(
    high_vol: dict[str, object],
    low_vol: dict[str, object],
) -> tuple[str, str]:
    raw_high = Decimal(str(high_vol["raw_post_cost_moderate"]))
    raw_low = Decimal(str(low_vol["raw_post_cost_moderate"]))
    vt_high = Decimal(str(high_vol["volatility_targeted_post_cost_moderate"]))
    vt_low = Decimal(str(low_vol["volatility_targeted_post_cost_moderate"]))
    if raw_high < Decimal("0") and raw_low > Decimal("0"):
        return (
            "real_regime_dependence",
            "Raw high_vol is also negative while raw low_vol is positive; regime dependence looks real.",
        )
    if (
        raw_high > Decimal("0")
        and raw_low > Decimal("0")
        and vt_high < Decimal("0")
        and vt_low > raw_low
    ):
        return (
            "normalization_artifact",
            "Raw buckets are both positive while volatility-targeted high_vol is negative and low_vol is amplified; concern may be normalization-driven.",
        )
    return (
        "inconclusive",
        "Raw and volatility-targeted regime buckets are mixed or ambiguous; normalization impact is inconclusive.",
    )


def _c5_split_has_pattern(high_vol: dict[str, object], low_vol: dict[str, object]) -> bool:
    raw_high = Decimal(str(high_vol["raw_post_cost_moderate"]))
    raw_low = Decimal(str(low_vol["raw_post_cost_moderate"]))
    vt_high = Decimal(str(high_vol["volatility_targeted_post_cost_moderate"]))
    vt_low = Decimal(str(low_vol["volatility_targeted_post_cost_moderate"]))
    return (
        raw_high < Decimal("0")
        and raw_low > Decimal("0")
        and vt_high < Decimal("0")
        and vt_low > Decimal("0")
    )


def _c5_interpretation(
    disc_high: dict[str, object],
    disc_low: dict[str, object],
    val_high: dict[str, object],
    val_low: dict[str, object],
) -> tuple[str, str]:
    disc_pattern = _c5_split_has_pattern(disc_high, disc_low)
    val_pattern = _c5_split_has_pattern(val_high, val_low)
    if disc_pattern and val_pattern:
        return (
            "structural_regime_dependence",
            "High_vol negative and low_vol positive in both discovery and validation "
            "using raw and volatility-targeted post-cost moderate; pattern appears structural.",
        )
    if disc_pattern or val_pattern:
        which = "discovery" if disc_pattern else "validation"
        return (
            "validation_only_or_discovery_only",
            f"Regime pattern (high_vol negative, low_vol positive) appears in {which} split only; "
            "pattern may not be structural.",
        )
    return (
        "inconclusive",
        "Regime dependence pattern is not consistently negative high_vol and positive low_vol "
        "in both splits; evidence is inconclusive.",
    )


def _c3_interpretation(
    lookback_results: dict[str, object],
    gate: dict[str, object],
) -> list[str]:
    primary = lookback_results[str(PRIMARY_LOOKBACK)]  # type: ignore[index]
    funding = primary["funding_stress"]["full"]  # type: ignore[index]
    high_cost_adjusted = Decimal(
        str(funding["high_cost"]["funding_adjusted_vt_post_cost_return"])
    )
    regime = primary["regime_decomposition"]["full"]  # type: ignore[index]
    high_vol = _primary_gate_metric_value(regime["high_vol"])
    low_vol = _primary_gate_metric_value(regime["low_vol"])
    return [
        (
            "Funding stress does not invalidate the 40-bar primary candidate "
            "under the tested scenarios."
            if high_cost_adjusted > Decimal("0")
            else "Funding stress would invalidate the 40-bar primary candidate under the tested scenarios."
        ),
        (
            "Regime decomposition shows a material regime-dependence concern: "
            f"high_vol is {high_vol} and low_vol is {low_vol}."
        ),
        f"Setup C remains {gate['decision']} research-only.",
        "Escalation to paper, runtime, trading, or live remains HOLD / NO-GO.",
        "No strategy filter is introduced by this diagnostic.",
        "Regime decomposition is observational only.",
    ]


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value
