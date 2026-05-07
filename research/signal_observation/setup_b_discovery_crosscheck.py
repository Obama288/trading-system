"""Stage 54-SQ-B8 discovery-window cross-check for Setup B 1R exit.

Research-only analysis over existing local 4H CSV files.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle
from .indicators import atr as compute_atr
from .setup_b import SignalDirection, SetupBObservation, detect_setup_b
from .setup_b_exit_research import (
    COST_SCENARIOS,
    VARIANT_A,
    ExitEntry,
    evaluate_exit_variant,
    load_bitget_4h_candles,
    load_json,
    metrics_for_outcomes,
)
from .setup_b_high_vol_validation import (
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    DISCOVERY_START,
    SYMBOLS,
    TIMEOUT_BARS,
    split_candles_at_discovery,
)


ATR_PERIOD = 14
P67 = Decimal("0.667")
B8_SURVIVES = "SURVIVES_AS_WEAK_PARKED_CANDIDATE"
B8_RETIRE = "RETIRE_HIGH_VOL_SETUP_B"
B8_TOO_FEW = "INCONCLUSIVE_TOO_FEW_DISCOVERY_OBSERVATIONS"
MIN_DISCOVERY_N = 15


@dataclass(frozen=True, slots=True)
class BucketSpec:
    """Sampling bucket for discovery-window random entries."""

    symbol: str
    direction: str
    count: int
    risk_distances: tuple[Decimal, ...]


def reconstruct_discovery_high_vol_entries(
    data_dir: str | Path,
) -> tuple[list[ExitEntry], dict[str, object], dict[str, list[Candle]]]:
    """Rebuild discovery-window high-vol Setup B entries from local 4H CSVs."""

    candles_by_symbol = load_bitget_4h_candles(data_dir)
    thresholds = _validation_atr_thresholds(candles_by_symbol)
    observations = _discovery_observations(candles_by_symbol)
    high_vol = [
        obs for obs in observations
        if obs.atr_at_entry >= thresholds[obs.symbol]
    ]
    entries = [_entry_from_observation(obs, candles_by_symbol[obs.symbol]) for obs in high_vol]
    reconstruction = {
        "window": "discovery",
        "discovery_start": DISCOVERY_START.isoformat(),
        "all_discovery_observations": len(observations),
        "high_vol_observations": len(entries),
        "atr_thresholds": thresholds,
        "symbol_direction_breakdown": symbol_direction_breakdown(entries),
        "source": "local_reconstruction_from_frozen_setup_b_and_validation_volatility_thresholds",
    }
    return entries, reconstruction, candles_by_symbol


def build_discovery_crosscheck_report(
    *,
    entries: Sequence[ExitEntry],
    candles_by_symbol: dict[str, list[Candle]],
    reconstruction: dict[str, object],
    b7_exit_artifact: dict[str, object],
    seed: int = DEFAULT_SEED,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, object]:
    """Build the B8 discovery-window 1R cross-check report."""

    outcomes = [
        evaluate_exit_variant(entry=entry, candles=candles_by_symbol[entry.symbol], variant=VARIANT_A)
        for entry in entries
    ]
    actual_metrics = metrics_for_outcomes(outcomes)
    random_summary = run_discovery_random_1r_baseline(
        entries=entries,
        candles_by_symbol=candles_by_symbol,
        seed=seed,
        iterations=iterations,
    )
    gate = evaluate_b8_gate(actual_metrics, random_summary)
    b7_side_by_side = _b7_validation_side_by_side(b7_exit_artifact)

    return _json_safe({
        "schema": "setup_b_discovery_crosscheck_v1",
        "scope": "analysis-only discovery-window cross-check over local 4H CSV files",
        "fixed_exit": "1R",
        "seed": seed,
        "iterations": iterations,
        "timeout_bars": TIMEOUT_BARS,
        "cost_scenarios": COST_SCENARIOS,
        "reconstruction": reconstruction,
        "actual_metrics": actual_metrics,
        "conditional_random_summary": random_summary,
        "b8_gate": gate,
        "b7_validation_side_by_side": b7_side_by_side,
        "interpretation": {
            "detector_changed": False,
            "entry_filter_data_changed": False,
            "variant_count": 1,
            "paper_trading_recommended": False,
            "live_trading_recommended": False,
        },
    })


def run_discovery_random_1r_baseline(
    *,
    entries: Sequence[ExitEntry],
    candles_by_symbol: dict[str, list[Candle]],
    seed: int = DEFAULT_SEED,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, object]:
    """Run matched discovery-window high-vol random baseline for fixed 1R."""

    eligible_indices = build_discovery_high_vol_eligible_indices(candles_by_symbol)
    bucket_specs = _build_bucket_specs(entries)
    rng = random.Random(seed)
    iteration_metrics: list[dict[str, object]] = []

    for _ in range(iterations):
        sampled_entries = _sample_random_entries(
            bucket_specs=bucket_specs,
            candles_by_symbol=candles_by_symbol,
            eligible_indices=eligible_indices,
            rng=rng,
        )
        outcomes = [
            evaluate_exit_variant(
                entry=entry,
                candles=candles_by_symbol[entry.symbol],
                variant=VARIANT_A,
            )
            for entry in sampled_entries
        ]
        iteration_metrics.append(metrics_for_outcomes(outcomes))

    return _summarize_random_iterations(iteration_metrics)


def build_discovery_high_vol_eligible_indices(
    candles_by_symbol: dict[str, list[Candle]],
    timeout_bars: int = TIMEOUT_BARS,
) -> dict[str, list[int]]:
    """Return discovery-window candle indexes with validation-calibrated high ATR."""

    thresholds = _validation_atr_thresholds(candles_by_symbol)
    val_candles_by_symbol, _ = split_candles_at_discovery(candles_by_symbol)
    eligible: dict[str, list[int]] = {}
    for symbol, candles in candles_by_symbol.items():
        val_count = len(val_candles_by_symbol[symbol])
        series = compute_atr(candles, ATR_PERIOD)
        max_index = len(candles) - timeout_bars - 1
        threshold = thresholds[symbol]
        eligible[symbol] = [
            index for index, value in enumerate(series)
            if index >= val_count
            and index <= max_index
            and value is not None
            and value >= threshold
        ]
    return eligible


def symbol_direction_breakdown(entries: Sequence[ExitEntry]) -> dict[str, int]:
    """Count entries by symbol and direction."""

    counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        counts[f"{entry.symbol}_{entry.direction}"] += 1
    return dict(sorted(counts.items()))


def evaluate_b8_gate(
    actual_metrics: dict[str, object],
    random_summary: dict[str, object],
) -> dict[str, object]:
    """Evaluate the B8 discovery-window pass gate."""

    n = int(actual_metrics["n"])
    actual_post = _optional_decimal(
        actual_metrics["post_cost_expectancy_r"]["moderate"]  # type: ignore[index]
    )
    random_post = random_summary.get("post_cost_expectancy_r", {})
    random_p75 = _optional_decimal(random_post.get("p75") if isinstance(random_post, dict) else None)

    n_ok = n >= MIN_DISCOVERY_N
    expectancy_ok = actual_post is not None and actual_post > Decimal("0")
    beats_random = (
        actual_post is not None and random_p75 is not None and actual_post > random_p75
    )
    if n < MIN_DISCOVERY_N:
        decision = B8_TOO_FEW
    elif n_ok and expectancy_ok and beats_random:
        decision = B8_SURVIVES
    else:
        decision = B8_RETIRE

    return {
        "decision": decision,
        "conditions": {
            "n_ge_15": n_ok,
            "post_cost_moderate_expectancy_gt_0": expectancy_ok,
            "beats_conditional_random_p75": beats_random,
        },
        "actual_post_cost_expectancy_moderate": actual_post,
        "random_p75_post_cost_expectancy_moderate": random_p75,
    }


def write_discovery_crosscheck_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic B8 artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_discovery_crosscheck_report(report), encoding="utf-8")
    json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_discovery_crosscheck_report(report: dict[str, object]) -> str:
    """Format a stable text report."""

    actual = report["actual_metrics"]
    random_summary = report["conditional_random_summary"]
    gate = report["b8_gate"]
    b7 = report["b7_validation_side_by_side"]
    random_post = random_summary["post_cost_expectancy_r"]
    lines = [
        "Setup B Stage B8 discovery-window cross-check",
        "",
        "Scope: analysis-only research over local 4H CSV files.",
        "No detector change, entry/filter/data change, runtime wiring, paper trading, or live trading.",
        "",
        f"discovery_start: {report['reconstruction']['discovery_start']}",
        f"discovery_high_vol_n: {report['reconstruction']['high_vol_observations']}",
        f"symbol_direction_breakdown: {report['reconstruction']['symbol_direction_breakdown']}",
        f"seed: {report['seed']}",
        f"iterations: {report['iterations']}",
        "",
        "Discovery fixed 1R metrics",
        f"  n: {actual['n']}",
        f"  wins/losses/flats: {actual['wins']}/{actual['losses']}/{actual['flats']}",
        f"  raw_expectancy_r: {actual['raw_expectancy_r']}",
        f"  post_cost_moderate_expectancy_r: {actual['post_cost_expectancy_r']['moderate']}",
        f"  random_p75_post_cost_moderate_expectancy_r: {random_post['p75']}",
        f"  win_rate: {actual['win_rate']}",
        f"  flat_rate: {actual['flat_rate']}",
        f"  avg_mfe_r: {actual['avg_mfe_r']}",
        f"  median_mfe_r: {actual['median_mfe_r']}",
        f"  avg_mae_r: {actual['avg_mae_r']}",
        f"  median_mae_r: {actual['median_mae_r']}",
        "",
        "B8 gate",
        f"  n_ge_15: {gate['conditions']['n_ge_15']}",
        f"  post_cost_moderate_expectancy_gt_0: {gate['conditions']['post_cost_moderate_expectancy_gt_0']}",
        f"  beats_conditional_random_p75: {gate['conditions']['beats_conditional_random_p75']}",
        f"  decision: {gate['decision']}",
        "",
        "B7 validation side-by-side",
        f"  validation_n: {b7['validation_n']}",
        f"  validation_post_cost_moderate_expectancy_r: {b7['validation_post_cost_moderate_expectancy_r']}",
        f"  validation_random_p75_post_cost_moderate_expectancy_r: {b7['validation_random_p75_post_cost_moderate_expectancy_r']}",
        "",
        "Interpretation",
        "  B8 is a cheap discovery-window cross-check only.",
        "  A pass does not authorize paper trading, live trading, or runtime wiring.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _discovery_observations(
    candles_by_symbol: dict[str, list[Candle]],
) -> list[SetupBObservation]:
    observations: list[SetupBObservation] = []
    for symbol in SYMBOLS:
        candles = candles_by_symbol[symbol]
        for direction in (SignalDirection.LONG, SignalDirection.SHORT):
            observations.extend(
                obs for obs in detect_setup_b(candles, symbol=symbol, direction=direction)
                if obs.signal_time >= DISCOVERY_START
            )
    return observations


def _entry_from_observation(obs: SetupBObservation, candles: Sequence[Candle]) -> ExitEntry:
    by_time = {candle.timestamp: index for index, candle in enumerate(candles)}
    if obs.entry_time not in by_time:
        raise ValueError(f"entry_time not found in candles: {obs.entry_time.isoformat()}")
    risk_distance = abs(obs.entry_price - obs.stop)
    if risk_distance <= Decimal("0"):
        raise ValueError("risk_distance must be positive")
    return ExitEntry(
        symbol=obs.symbol,
        direction=obs.signal_direction.value,
        entry_index=by_time[obs.entry_time],
        entry_time=obs.entry_time,
        entry_price=obs.entry_price,
        stop=obs.stop,
        risk_distance=risk_distance,
    )


def _validation_atr_thresholds(
    candles_by_symbol: dict[str, list[Candle]],
) -> dict[str, Decimal]:
    thresholds: dict[str, Decimal] = {}
    val_candles_by_symbol, _ = split_candles_at_discovery(candles_by_symbol)
    for symbol, candles in candles_by_symbol.items():
        val_count = len(val_candles_by_symbol[symbol])
        series = compute_atr(candles, ATR_PERIOD)
        values = sorted(value for value in series[:val_count] if value is not None)
        if len(values) < 3:
            raise ValueError(f"not enough validation ATR values for {symbol}")
        thresholds[symbol] = _percentile(values, P67)
    return thresholds


def _build_bucket_specs(entries: Sequence[ExitEntry]) -> list[BucketSpec]:
    grouped: dict[tuple[str, str], list[Decimal]] = defaultdict(list)
    for entry in entries:
        grouped[(entry.symbol, entry.direction)].append(entry.risk_distance)
    return [
        BucketSpec(symbol, direction, len(risks), tuple(risks))
        for (symbol, direction), risks in sorted(grouped.items())
    ]


def _sample_random_entries(
    *,
    bucket_specs: Sequence[BucketSpec],
    candles_by_symbol: dict[str, Sequence[Candle]],
    eligible_indices: dict[str, list[int]],
    rng: random.Random,
) -> list[ExitEntry]:
    entries: list[ExitEntry] = []
    for spec in bucket_specs:
        eligible = eligible_indices.get(spec.symbol, [])
        if not eligible:
            raise ValueError(f"no discovery high-vol eligible candles for {spec.symbol}")
        candles = candles_by_symbol[spec.symbol]
        for _ in range(spec.count):
            entry_index = rng.choice(eligible)
            risk = rng.choice(spec.risk_distances)
            candle = candles[entry_index]
            stop = candle.close - risk if spec.direction == "long" else candle.close + risk
            entries.append(
                ExitEntry(
                    symbol=spec.symbol,
                    direction=spec.direction,
                    entry_index=entry_index,
                    entry_time=candle.timestamp,
                    entry_price=candle.close,
                    stop=stop,
                    risk_distance=risk,
                )
            )
    return entries


def _summarize_random_iterations(
    metrics: Sequence[dict[str, object]],
) -> dict[str, object]:
    return {
        "expectancy_r": _distribution(
            [_optional_decimal(item.get("raw_expectancy_r")) for item in metrics]
        ),
        "post_cost_expectancy_r": _distribution(
            [
                _optional_decimal(item["post_cost_expectancy_r"]["moderate"])  # type: ignore[index]
                for item in metrics
            ]
        ),
        "win_rate": _distribution([_optional_decimal(item.get("win_rate")) for item in metrics]),
        "flat_rate": _distribution([_optional_decimal(item.get("flat_rate")) for item in metrics]),
        "avg_mfe_r": _distribution([_optional_decimal(item.get("avg_mfe_r")) for item in metrics]),
    }


def _b7_validation_side_by_side(artifact: dict[str, object]) -> dict[str, object]:
    actual = artifact["actual_metrics"][VARIANT_A]  # type: ignore[index]
    random_summary = artifact["conditional_random_summary"][VARIANT_A]  # type: ignore[index]
    random_post = random_summary["post_cost_expectancy_r"]
    return {
        "validation_n": actual["n"],
        "validation_post_cost_moderate_expectancy_r": actual["post_cost_expectancy_r"]["moderate"],
        "validation_random_p75_post_cost_moderate_expectancy_r": random_post["p75"],
    }


def _distribution(values: Sequence[Decimal | None]) -> dict[str, Decimal | None]:
    clean = [value for value in values if value is not None]
    if not clean:
        return {"median": None, "p75": None, "p90": None, "min": None, "max": None}
    sorted_values = sorted(clean)
    return {
        "median": _median(sorted_values),
        "p75": _percentile(sorted_values, Decimal("0.75")),
        "p90": _percentile(sorted_values, Decimal("0.90")),
        "min": sorted_values[0],
        "max": sorted_values[-1],
    }


def _percentile(values: Sequence[Decimal], percentile: Decimal) -> Decimal:
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    rank = percentile * Decimal(len(sorted_values) - 1)
    lower = int(rank.to_integral_value(rounding="ROUND_FLOOR"))
    upper = int(rank.to_integral_value(rounding="ROUND_CEILING"))
    if lower == upper:
        return sorted_values[lower]
    fraction = rank - Decimal(lower)
    return sorted_values[lower] + (
        (sorted_values[upper] - sorted_values[lower]) * fraction
    )


def _median(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / Decimal("2")


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
