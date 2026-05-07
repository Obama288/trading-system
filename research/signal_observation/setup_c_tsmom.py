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
                previous_direction = direction
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
    for lookback in LOOKBACKS:
        intervals = build_tsmom_intervals(candles_by_symbol, lookback=lookback)
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
        "random_seed": seed,
        "random_iterations": random_iterations,
        "cost_bps_per_turnover": _json_safe(COST_BPS),
        "funding_costs_excluded": True,
        "lookbacks": lookback_results,
        "autocorrelation_diagnostics": autocorrelation,
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
    direction_counts = Counter(item.direction for item in intervals)
    turnover_total = sum(item.turnover_units for item in intervals)
    gross_total = sum(gross_returns, Decimal("0"))
    moderate_cost_total = sum(
        cost_return(item.turnover_units, COST_BPS["moderate"])
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
            "post_cost_return": {
                scenario: sum(values, Decimal("0"))
                for scenario, values in scenario_returns.items()
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
            "max_drawdown_like": _max_drawdown(gross_returns),
            "cost_to_gross_ratio_moderate": (
                moderate_cost_total / abs(gross_total)
                if gross_total != Decimal("0")
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
    for iteration in range(iterations):
        rng = random.Random(seed + iteration)
        randomized = _randomized_intervals(template_intervals, rng)
        split_values["full"].append(_post_cost_total(randomized, "moderate"))
        split_values["discovery"].append(
            _post_cost_total(
                [item for item in randomized if item.split == "discovery"],
                "moderate",
            )
        )
        split_values["validation"].append(
            _post_cost_total(
                [item for item in randomized if item.split == "validation"],
                "moderate",
            )
        )

    return _json_safe(
        {
            split: {
                "median": _median(values),
                "p75": _percentile(values, Decimal("0.75")),
                "p90": _percentile(values, Decimal("0.90")),
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
    discovery_post_cost = Decimal(str(discovery["post_cost_return"]["moderate"]))
    validation_post_cost = Decimal(str(validation["post_cost_return"]["moderate"]))
    random_discovery = random_summary["discovery"]  # type: ignore[index]
    random_median = Decimal(str(random_discovery["median"]))
    random_p75 = Decimal(str(random_discovery["p75"]))
    positive_symbols = sum(
        1
        for symbol_metrics in per_symbol_full.values()
        if Decimal(str(symbol_metrics["post_cost_return"]["moderate"])) > Decimal("0")
    )
    cost_ratio_value = metrics["full"]["cost_to_gross_ratio_moderate"]  # type: ignore[index]
    costs_do_not_dominate = (
        cost_ratio_value is not None
        and Decimal(str(cost_ratio_value)) <= Decimal("0.50")
    )
    gate_results = {
        "discovery_post_cost_moderate_gt_0": discovery_post_cost > Decimal("0"),
        "beats_random_median": discovery_post_cost > random_median,
        "beats_random_p75": discovery_post_cost > random_p75,
        "two_of_three_symbols_positive": positive_symbols >= 2,
        "costs_do_not_dominate_gross": costs_do_not_dominate,
        "validation_post_cost_moderate_gte_0": validation_post_cost >= Decimal("0"),
    }

    sensitivity_better_than_primary = _sensitivity_better_than_primary(lookback_results)
    passes = (
        gate_results["discovery_post_cost_moderate_gt_0"]
        and gate_results["beats_random_p75"]
        and gate_results["two_of_three_symbols_positive"]
        and gate_results["costs_do_not_dominate_gross"]
        and gate_results["validation_post_cost_moderate_gte_0"]
    )
    if passes:
        decision = RESULT_PASS
    elif (
        not gate_results["discovery_post_cost_moderate_gt_0"]
        or not gate_results["beats_random_median"]
        or not gate_results["two_of_three_symbols_positive"]
        or not gate_results["costs_do_not_dominate_gross"]
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
            "gate_results": gate_results,
            "positive_symbol_count": positive_symbols,
            "sensitivity_better_than_primary": sensitivity_better_than_primary,
            "notes": [
                "PASS is research-only and not paper-ready",
                "funding costs excluded",
                "moderate cost is the primary gate",
            ],
        }
    )


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
        "",
        "Lookback summaries",
    ]
    lookbacks = report["lookbacks"]  # type: ignore[assignment]
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
                f"  discovery_post_cost_moderate: {discovery['post_cost_return']['moderate']}",
                f"  validation_post_cost_moderate: {validation['post_cost_return']['moderate']}",
                f"  full_post_cost_moderate: {full['post_cost_return']['moderate']}",
                f"  discovery_random_median/p75/p90: "
                f"{random_summary['median']} / {random_summary['p75']} / {random_summary['p90']}",
                f"  turnover: {full['turnover']}",
                f"  cost_to_gross_ratio_moderate: {full['cost_to_gross_ratio_moderate']}",
            ]
        )
        lines.append("  per_symbol_full_post_cost_moderate:")
        for symbol, symbol_metrics in sorted(item["per_symbol"]["full"].items()):
            lines.append(
                f"    {symbol}: {symbol_metrics['post_cost_return']['moderate']}"
            )

    lines.extend(["", "Primary gate"])
    gate = report["gate"]  # type: ignore[assignment]
    for key, value in gate["gate_results"].items():
        lines.append(f"  {key}: {value}")

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


def _sign(value: Decimal) -> int:
    if value > Decimal("0"):
        return 1
    if value < Decimal("0"):
        return -1
    return 0


def _sensitivity_better_than_primary(lookback_results: dict[str, object]) -> bool:
    primary = lookback_results[str(PRIMARY_LOOKBACK)]  # type: ignore[index]
    primary_value = Decimal(
        str(primary["metrics"]["discovery"]["post_cost_return"]["moderate"])  # type: ignore[index]
    )
    for lookback in ("20", "60"):
        value = Decimal(
            str(
                lookback_results[lookback]["metrics"]["discovery"]["post_cost_return"]["moderate"]  # type: ignore[index]
            )
        )
        if value > primary_value:
            return True
    return False


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
