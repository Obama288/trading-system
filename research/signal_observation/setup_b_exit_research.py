"""Stage 54-SQ-B7 bounded exit research for frozen high-vol Setup B.

Research-only analysis over local 4H CSV files and existing validation rules.
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
from .csv_loader import load_ohlcv_csv
from .setup_b import OUTCOME_WINDOW_CANDLES, SignalDirection
from .setup_b_high_vol_validation import (
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    PRODUCT_TYPE,
    SYMBOLS,
    TIMEOUT_BARS,
    build_vol_high_eligible_indices,
    run_validation_observations,
    split_candles_at_discovery,
    tag_high_vol_validation,
)


EXPECTED_HIGH_VOL_N = 62
COST_SCENARIOS: dict[str, Decimal] = {
    "optimistic": Decimal("0.04"),
    "moderate": Decimal("0.08"),
    "conservative": Decimal("0.12"),
}
VARIANT_A = "A_FIXED_1R"
VARIANT_B = "B_PROTECTIVE_AFTER_0_7R"
VARIANT_C = "C_BREAKEVEN_AFTER_1R"
VARIANTS = (VARIANT_A, VARIANT_B, VARIANT_C)
B7_CANDIDATE = "EXIT_VARIANT_RESEARCH_CANDIDATE"
B7_RETIRE = "RETIRE_HIGH_VOL_SETUP_B"
PROTECTIVE_ACTIVATION_R = Decimal("0.7")
PROTECTIVE_EXIT_R = Decimal("0.3")
BREAKEVEN_ACTIVATION_R = Decimal("1")
TARGET_R_BY_VARIANT = {
    VARIANT_A: Decimal("1"),
    VARIANT_B: Decimal("1.5"),
    VARIANT_C: Decimal("1.5"),
}


@dataclass(frozen=True, slots=True)
class ExitEntry:
    """Frozen entry used for B7 exit research."""

    symbol: str
    direction: str
    entry_index: int
    entry_time: datetime
    entry_price: Decimal
    stop: Decimal
    risk_distance: Decimal


@dataclass(frozen=True, slots=True)
class ExitOutcome:
    """Outcome from one B7 exit variant."""

    variant: str
    outcome: str
    result_r: Decimal
    mae_r: Decimal
    mfe_r: Decimal
    bars_to_resolution: int


@dataclass(frozen=True, slots=True)
class BucketSpec:
    """Sampling bucket for matched random entries."""

    symbol: str
    direction: str
    count: int
    risk_distances: tuple[Decimal, ...]


def load_bitget_4h_candles(data_dir: str | Path) -> dict[str, list[Candle]]:
    """Load local Bitget 4H CSV files for the frozen B7 universe."""

    base = Path(data_dir)
    return {
        symbol: load_ohlcv_csv(base / f"{symbol}_{PRODUCT_TYPE}_4H.csv")
        for symbol in SYMBOLS
    }


def reconstruct_high_vol_entries(
    data_dir: str | Path,
) -> tuple[list[ExitEntry], dict[str, object], dict[str, list[Candle]]]:
    """Reconstruct B5 high-vol validation rows and attach candle indexes."""

    candles_by_symbol = load_bitget_4h_candles(data_dir)
    validation_observations = run_validation_observations(candles_by_symbol)
    tagged, threshold_info = tag_high_vol_validation(
        validation_observations,
        candles_by_symbol,
    )
    high_vol = [obs for obs in tagged if obs.get("tag_volatility_regime") == "high"]
    entries = [
        _entry_from_observation(obs, candles_by_symbol[str(obs["symbol"])])
        for obs in high_vol
    ]
    reconstruction = {
        "expected_n": EXPECTED_HIGH_VOL_N,
        "reconstructed_n": len(entries),
        "matched_expected_n": len(entries) == EXPECTED_HIGH_VOL_N,
        "all_validation_observations": len(validation_observations),
        "atr_threshold_info": threshold_info,
        "source": "local_reconstruction_from_frozen_b5_logic",
    }
    return entries, reconstruction, candles_by_symbol


def build_exit_research_report(
    *,
    entries: Sequence[ExitEntry],
    candles_by_symbol: dict[str, list[Candle]],
    reconstruction: dict[str, object],
    seed: int = DEFAULT_SEED,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, object]:
    """Evaluate all frozen B7 variants and matched conditional random baselines."""

    if len(entries) != EXPECTED_HIGH_VOL_N:
        raise ValueError(
            "B7 reconstruction mismatch: "
            f"expected {EXPECTED_HIGH_VOL_N}, got {len(entries)}"
        )

    actual = {
        variant: metrics_for_outcomes(
            [
                evaluate_exit_variant(
                    entry=entry,
                    candles=candles_by_symbol[entry.symbol],
                    variant=variant,
                )
                for entry in entries
            ]
        )
        for variant in VARIANTS
    }

    random_summary = run_conditional_random_exit_baseline(
        entries=entries,
        candles_by_symbol=candles_by_symbol,
        seed=seed,
        iterations=iterations,
    )
    gates = {
        variant: evaluate_variant_gate(actual[variant], random_summary[variant])
        for variant in VARIANTS
    }
    decision = (
        B7_CANDIDATE
        if any(gate["passes"] for gate in gates.values())
        else B7_RETIRE
    )

    return _json_safe({
        "schema": "setup_b_exit_research_v1",
        "scope": "analysis-only bounded exit research over reconstructed high-vol validation entries",
        "reconstruction": reconstruction,
        "seed": seed,
        "iterations": iterations,
        "timeout_bars": OUTCOME_WINDOW_CANDLES,
        "cost_scenarios": COST_SCENARIOS,
        "variants": {
            VARIANT_A: {
                "label": "Fixed 1R target",
                "target_r": "1",
                "overfitting_risk": "standard_frozen_design_variant",
            },
            VARIANT_B: {
                "label": "Protective pullback after 0.7R",
                "target_r": "1.5",
                "activation_r": PROTECTIVE_ACTIVATION_R,
                "exit_r": PROTECTIVE_EXIT_R,
                "overfitting_risk": "B6_diagnostic_inspired_higher_risk",
            },
            VARIANT_C: {
                "label": "Breakeven after 1R",
                "target_r": "1.5",
                "activation_r": BREAKEVEN_ACTIVATION_R,
                "overfitting_risk": "standard_frozen_design_variant",
            },
        },
        "actual_metrics": actual,
        "conditional_random_summary": random_summary,
        "gate_by_variant": gates,
        "b7_decision": {
            "decision": decision,
            "paper_trading_recommended": False,
            "live_trading_recommended": False,
            "no_rescue_stage_if_failed": decision == B7_RETIRE,
        },
        "interpretation": {
            "entry_filter_data_changed": False,
            "variant_count": len(VARIANTS),
            "variant_b_threshold_provenance": "B6 flat-MFE diagnostics; higher overfitting risk",
            "readiness_claim": "research_candidate_only_if_gate_passes",
        },
    })


def evaluate_exit_variant(
    *,
    entry: ExitEntry,
    candles: Sequence[Candle],
    variant: str,
    timeout_bars: int = OUTCOME_WINDOW_CANDLES,
) -> ExitOutcome:
    """Resolve one entry under one frozen B7 exit variant."""

    if variant not in VARIANTS:
        raise ValueError(f"unsupported variant: {variant}")
    window = candles[entry.entry_index + 1 : entry.entry_index + 1 + timeout_bars]
    target_r = TARGET_R_BY_VARIANT[variant]
    target = _target_price(entry.entry_price, entry.risk_distance, target_r, entry.direction)

    if variant == VARIANT_A:
        return _resolve_fixed_target(
            variant=variant,
            window=window,
            entry_price=entry.entry_price,
            stop=entry.stop,
            target=target,
            target_r=target_r,
            risk_distance=entry.risk_distance,
            direction=entry.direction,
        )
    if variant == VARIANT_B:
        return _resolve_protective(
            window=window,
            entry_price=entry.entry_price,
            stop=entry.stop,
            target=target,
            risk_distance=entry.risk_distance,
            direction=entry.direction,
        )
    return _resolve_breakeven(
        window=window,
        entry_price=entry.entry_price,
        stop=entry.stop,
        target=target,
        risk_distance=entry.risk_distance,
        direction=entry.direction,
    )


def metrics_for_outcomes(outcomes: Sequence[ExitOutcome]) -> dict[str, object]:
    """Compute B7 metrics for a collection of variant outcomes."""

    values = [outcome.result_r for outcome in outcomes]
    wins = sum(1 for value in values if value > Decimal("0"))
    losses = sum(1 for value in values if value < Decimal("0"))
    flats = sum(1 for value in values if value == Decimal("0"))
    n = len(values)
    mfe_values = [outcome.mfe_r for outcome in outcomes]
    mae_values = [outcome.mae_r for outcome in outcomes]
    bars_values = [Decimal(outcome.bars_to_resolution) for outcome in outcomes]
    post_cost = {
        name: _post_cost_metrics(values, cost_r)
        for name, cost_r in COST_SCENARIOS.items()
    }
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": _rate(wins, n),
        "flat_rate": _rate(flats, n),
        "raw_expectancy_r": _average(values),
        "post_cost_expectancy_r": {
            name: metrics["expectancy_r"] for name, metrics in post_cost.items()
        },
        "raw_profit_factor": _profit_factor(values),
        "post_cost_profit_factor": {
            name: metrics["profit_factor"] for name, metrics in post_cost.items()
        },
        "avg_mfe_r": _average(mfe_values),
        "median_mfe_r": _median(mfe_values),
        "avg_mae_r": _average(mae_values),
        "median_mae_r": _median(mae_values),
        "avg_bars_to_resolution": _average(bars_values),
        "median_bars_to_resolution": _median(bars_values),
    }


def run_conditional_random_exit_baseline(
    *,
    entries: Sequence[ExitEntry],
    candles_by_symbol: dict[str, list[Candle]],
    seed: int = DEFAULT_SEED,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, object]:
    """Run matched high-vol random baselines under each B7 variant."""

    val_candles_by_symbol, _ = split_candles_at_discovery(candles_by_symbol)
    eligible_indices = build_vol_high_eligible_indices(
        candles_by_symbol,
        val_candles_by_symbol,
        timeout_bars=TIMEOUT_BARS,
    )
    bucket_specs = _build_bucket_specs(entries)
    rng = random.Random(seed)
    iteration_metrics: dict[str, list[dict[str, object]]] = {
        variant: [] for variant in VARIANTS
    }

    for _ in range(iterations):
        random_entries = _sample_random_entries(
            bucket_specs=bucket_specs,
            candles_by_symbol=candles_by_symbol,
            eligible_indices=eligible_indices,
            rng=rng,
        )
        for variant in VARIANTS:
            outcomes = [
                evaluate_exit_variant(
                    entry=random_entry,
                    candles=candles_by_symbol[random_entry.symbol],
                    variant=variant,
                )
                for random_entry in random_entries
            ]
            iteration_metrics[variant].append(metrics_for_outcomes(outcomes))

    return {
        variant: _summarize_random_iterations(iteration_metrics[variant])
        for variant in VARIANTS
    }


def evaluate_variant_gate(
    actual_metrics: dict[str, object],
    random_summary: dict[str, object],
) -> dict[str, object]:
    """Evaluate the B7 pass gate for one variant."""

    actual_post = _optional_decimal(
        actual_metrics["post_cost_expectancy_r"]["moderate"]  # type: ignore[index]
    )
    random_post = random_summary.get("post_cost_expectancy_r", {})
    random_p75 = _optional_decimal(random_post.get("p75") if isinstance(random_post, dict) else None)
    n = int(actual_metrics["n"])
    passes = (
        n == EXPECTED_HIGH_VOL_N
        and actual_post is not None
        and actual_post > Decimal("0")
        and random_p75 is not None
        and actual_post > random_p75
    )
    return {
        "passes": passes,
        "conditions": {
            "n_remains_62": n == EXPECTED_HIGH_VOL_N,
            "post_cost_expectancy_moderate_positive": (
                actual_post is not None and actual_post > Decimal("0")
            ),
            "beats_random_p75_post_cost_moderate": (
                actual_post is not None and random_p75 is not None and actual_post > random_p75
            ),
            "entry_filter_data_unchanged": True,
            "research_candidate_only": True,
        },
        "actual_post_cost_expectancy_moderate": actual_post,
        "random_p75_post_cost_expectancy_moderate": random_p75,
    }


def write_exit_research_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic B7 artifacts."""

    text_out = Path(text_path)
    json_out = Path(json_path)
    text_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    text_out.write_text(format_exit_research_report(report), encoding="utf-8")
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_exit_research_report(report: dict[str, object]) -> str:
    """Format a stable text report."""

    lines = [
        "Setup B Stage B7 bounded exit research",
        "",
        "Scope: analysis-only research over frozen high-vol validation entries.",
        "No detector change, entry/filter/data change, runtime wiring, paper trading, or live trading.",
        "",
        f"reconstructed_n: {report['reconstruction']['reconstructed_n']}",
        f"matched_expected_n: {report['reconstruction']['matched_expected_n']}",
        f"seed: {report['seed']}",
        f"iterations: {report['iterations']}",
        f"timeout_bars: {report['timeout_bars']}",
        "",
        "Variant metrics",
    ]
    actual = report["actual_metrics"]
    random_summary = report["conditional_random_summary"]
    gates = report["gate_by_variant"]
    for variant in VARIANTS:
        metrics = actual[variant]
        random_metrics = random_summary[variant]
        gate = gates[variant]
        rand_post = random_metrics["post_cost_expectancy_r"]
        lines.extend([
            f"  {variant}",
            f"    n: {metrics['n']}",
            f"    wins/losses/flats: {metrics['wins']}/{metrics['losses']}/{metrics['flats']}",
            f"    raw_expectancy_r: {metrics['raw_expectancy_r']}",
            f"    post_cost_moderate_expectancy_r: {metrics['post_cost_expectancy_r']['moderate']}",
            f"    random_p75_post_cost_moderate_expectancy_r: {rand_post['p75']}",
            f"    flat_rate: {metrics['flat_rate']}",
            f"    avg_mfe_r: {metrics['avg_mfe_r']}",
            f"    median_mfe_r: {metrics['median_mfe_r']}",
            f"    avg_mae_r: {metrics['avg_mae_r']}",
            f"    median_mae_r: {metrics['median_mae_r']}",
            f"    gate_passes: {gate['passes']}",
        ])
        if variant == VARIANT_B:
            lines.append(
                "    threshold_provenance: B6 flat-MFE diagnostics; higher overfitting risk"
            )

    decision = report["b7_decision"]
    lines.extend([
        "",
        "B7 decision",
        f"  decision: {decision['decision']}",
        f"  paper_trading_recommended: {decision['paper_trading_recommended']}",
        f"  live_trading_recommended: {decision['live_trading_recommended']}",
        "",
        "Interpretation",
        "  Each variant was compared with a matched high-vol random baseline under the same exit logic.",
        "  A pass is a research candidate only, not readiness for paper trading or live trading.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def load_json(path: str | Path) -> dict[str, object]:
    """Load a JSON object."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _entry_from_observation(
    obs: dict[str, object],
    candles: Sequence[Candle],
) -> ExitEntry:
    entry_time = _parse_timestamp(str(obs["entry_time"]))
    by_time = {candle.timestamp: index for index, candle in enumerate(candles)}
    if entry_time not in by_time:
        raise ValueError(f"entry_time not found in candles: {entry_time.isoformat()}")
    entry_price = Decimal(str(obs["entry_price"]))
    stop = Decimal(str(obs["stop"]))
    risk_distance = abs(entry_price - stop)
    if risk_distance <= Decimal("0"):
        raise ValueError("risk_distance must be positive")
    direction = str(obs["signal_direction"])
    if direction not in {SignalDirection.LONG.value, SignalDirection.SHORT.value}:
        raise ValueError(f"unsupported direction: {direction}")
    return ExitEntry(
        symbol=str(obs["symbol"]),
        direction=direction,
        entry_index=by_time[entry_time],
        entry_time=entry_time,
        entry_price=entry_price,
        stop=stop,
        risk_distance=risk_distance,
    )


def _resolve_fixed_target(
    *,
    variant: str,
    window: Sequence[Candle],
    entry_price: Decimal,
    stop: Decimal,
    target: Decimal,
    target_r: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> ExitOutcome:
    if not window:
        return ExitOutcome(variant, "flat", Decimal("0"), Decimal("0"), Decimal("0"), 0)

    for offset, candle in enumerate(window, start=1):
        slice_now = window[:offset]
        if _stop_hit(candle, stop, direction):
            mae, mfe = _excursions(slice_now, entry_price, risk_distance, direction)
            return ExitOutcome(variant, "loss", Decimal("-1"), mae, mfe, offset)
        if _target_hit(candle, target, direction):
            mae, mfe = _excursions(slice_now, entry_price, risk_distance, direction)
            return ExitOutcome(variant, "win", target_r, mae, mfe, offset)

    mae, mfe = _excursions(window, entry_price, risk_distance, direction)
    return ExitOutcome(variant, "flat", Decimal("0"), mae, mfe, len(window))


def _resolve_protective(
    *,
    window: Sequence[Candle],
    entry_price: Decimal,
    stop: Decimal,
    target: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> ExitOutcome:
    variant = VARIANT_B
    if not window:
        return ExitOutcome(variant, "flat", Decimal("0"), Decimal("0"), Decimal("0"), 0)

    activation = _target_price(
        entry_price, risk_distance, PROTECTIVE_ACTIVATION_R, direction
    )
    protective_exit = _target_price(entry_price, risk_distance, PROTECTIVE_EXIT_R, direction)
    activated = False
    for offset, candle in enumerate(window, start=1):
        slice_now = window[:offset]
        if _stop_hit(candle, stop, direction):
            mae, mfe = _excursions(slice_now, entry_price, risk_distance, direction)
            return ExitOutcome(variant, "loss", Decimal("-1"), mae, mfe, offset)
        if _target_hit(candle, target, direction):
            mae, mfe = _excursions(slice_now, entry_price, risk_distance, direction)
            return ExitOutcome(variant, "win", Decimal("1.5"), mae, mfe, offset)
        if not activated and _target_hit(candle, activation, direction):
            activated = True
        if activated and _protective_exit_hit(candle, protective_exit, direction):
            mae, mfe = _excursions(slice_now, entry_price, risk_distance, direction)
            return ExitOutcome(variant, "win", PROTECTIVE_EXIT_R, mae, mfe, offset)

    mae, mfe = _excursions(window, entry_price, risk_distance, direction)
    return ExitOutcome(variant, "flat", Decimal("0"), mae, mfe, len(window))


def _resolve_breakeven(
    *,
    window: Sequence[Candle],
    entry_price: Decimal,
    stop: Decimal,
    target: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> ExitOutcome:
    variant = VARIANT_C
    if not window:
        return ExitOutcome(variant, "flat", Decimal("0"), Decimal("0"), Decimal("0"), 0)

    activation = _target_price(entry_price, risk_distance, BREAKEVEN_ACTIVATION_R, direction)
    activated = False
    for offset, candle in enumerate(window, start=1):
        slice_now = window[:offset]
        active_stop = entry_price if activated else stop
        if _stop_hit(candle, active_stop, direction):
            mae, mfe = _excursions(slice_now, entry_price, risk_distance, direction)
            result_r = Decimal("0") if activated else Decimal("-1")
            outcome = "flat" if activated else "loss"
            return ExitOutcome(variant, outcome, result_r, mae, mfe, offset)
        if _target_hit(candle, target, direction):
            mae, mfe = _excursions(slice_now, entry_price, risk_distance, direction)
            return ExitOutcome(variant, "win", Decimal("1.5"), mae, mfe, offset)
        if not activated and _target_hit(candle, activation, direction):
            activated = True

    mae, mfe = _excursions(window, entry_price, risk_distance, direction)
    return ExitOutcome(variant, "flat", Decimal("0"), mae, mfe, len(window))


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
            raise ValueError(f"no high-vol eligible candles for {spec.symbol}")
        candles = candles_by_symbol[spec.symbol]
        for _ in range(spec.count):
            entry_index = rng.choice(eligible)
            risk = rng.choice(spec.risk_distances)
            candle = candles[entry_index]
            if spec.direction == SignalDirection.LONG.value:
                stop = candle.close - risk
            else:
                stop = candle.close + risk
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


def _post_cost_metrics(values: Sequence[Decimal], cost_r: Decimal) -> dict[str, Decimal | None]:
    adjusted = [value - cost_r for value in values]
    return {
        "expectancy_r": _average(adjusted),
        "profit_factor": _profit_factor(adjusted),
    }


def _target_price(
    entry_price: Decimal,
    risk_distance: Decimal,
    target_r: Decimal,
    direction: str,
) -> Decimal:
    if direction == SignalDirection.LONG.value:
        return entry_price + (risk_distance * target_r)
    return entry_price - (risk_distance * target_r)


def _stop_hit(candle: Candle, stop: Decimal, direction: str) -> bool:
    if direction == SignalDirection.LONG.value:
        return candle.low <= stop
    return candle.high >= stop


def _target_hit(candle: Candle, target: Decimal, direction: str) -> bool:
    if direction == SignalDirection.LONG.value:
        return candle.high >= target
    return candle.low <= target


def _protective_exit_hit(candle: Candle, exit_price: Decimal, direction: str) -> bool:
    if direction == SignalDirection.LONG.value:
        return candle.low <= exit_price
    return candle.high >= exit_price


def _excursions(
    window: Sequence[Candle],
    entry_price: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> tuple[Decimal, Decimal]:
    if not window:
        return Decimal("0"), Decimal("0")
    if direction == SignalDirection.LONG.value:
        mfe = max((candle.high - entry_price) / risk_distance for candle in window)
        mae = min((candle.low - entry_price) / risk_distance for candle in window)
    else:
        mfe = max((entry_price - candle.low) / risk_distance for candle in window)
        mae = min((entry_price - candle.high) / risk_distance for candle in window)
    return mae, mfe


def _profit_factor(values: Sequence[Decimal]) -> Decimal | None:
    wins = sum((value for value in values if value > Decimal("0")), Decimal("0"))
    losses = abs(sum((value for value in values if value < Decimal("0")), Decimal("0")))
    if wins <= Decimal("0") or losses <= Decimal("0"):
        return None
    return wins / losses


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


def _percentile(values: Sequence[Decimal], percentile: Decimal) -> Decimal | None:
    if not values:
        return None
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


def _rate(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return Decimal(count) / Decimal(total)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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
