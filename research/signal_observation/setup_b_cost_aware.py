"""Stage 54-SQ-B6 cost-aware evidence report for Setup B.

Research-only analysis over existing local artifacts and CSV files.
No detector changes, downloads, private API, runtime wiring, or execution.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .csv_loader import load_ohlcv_csv
from .setup_b_high_vol_validation import (
    PRODUCT_TYPE,
    SYMBOLS,
    VALIDATION_TARGET,
    compute_validation_metrics,
    run_validation_observations,
    tag_high_vol_validation,
)


EXPECTED_HIGH_VOL_N = 62
COST_SCENARIOS: dict[str, Decimal] = {
    "optimistic": Decimal("0.04"),
    "moderate": Decimal("0.08"),
    "conservative": Decimal("0.12"),
}
B6_RETIRE = "RETIRE_HIGH_VOL_SETUP_B"
B6_LONG_SHOT = "B7_EXIT_RESEARCH_LONG_SHOT"
B6_CANDIDATE = "B7_EXIT_RESEARCH_CANDIDATE"


def reconstruct_validation_high_vol_subset(
    data_dir: str | Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Rebuild the frozen B5 high-vol validation subset from local 4H CSVs."""

    base = Path(data_dir)
    candles_by_symbol = {
        symbol: load_ohlcv_csv(base / f"{symbol}_{PRODUCT_TYPE}_4H.csv")
        for symbol in SYMBOLS
    }
    validation_observations = run_validation_observations(candles_by_symbol)
    tagged, atr_threshold_info = tag_high_vol_validation(
        validation_observations,
        candles_by_symbol,
    )
    high_vol = [
        obs for obs in tagged
        if obs.get("tag_volatility_regime") == "high"
    ]
    reconstruction = {
        "expected_n": EXPECTED_HIGH_VOL_N,
        "reconstructed_n": len(high_vol),
        "matched_expected_n": len(high_vol) == EXPECTED_HIGH_VOL_N,
        "all_validation_observations": len(validation_observations),
        "atr_threshold_info": atr_threshold_info,
    }
    return high_vol, reconstruction


def build_cost_aware_report(
    *,
    high_vol_observations: Sequence[dict[str, object]],
    validation_artifact: dict[str, object],
) -> dict[str, object]:
    """Build the B6 report from reconstructed observations and B5 random summary."""

    if len(high_vol_observations) != EXPECTED_HIGH_VOL_N:
        raise ValueError(
            "reconstructed validation high-vol subset mismatch: "
            f"expected {EXPECTED_HIGH_VOL_N}, got {len(high_vol_observations)}"
        )

    actual_metrics = compute_validation_metrics(high_vol_observations)
    raw_target_metrics = actual_metrics[VALIDATION_TARGET]
    random_summary = validation_artifact.get("random_summary", {})
    random_target = (
        random_summary.get(VALIDATION_TARGET, {})
        if isinstance(random_summary, dict)
        else {}
    )

    post_cost = {
        name: post_cost_metrics(high_vol_observations, cost_r)
        for name, cost_r in COST_SCENARIOS.items()
    }
    random_post_cost = {
        name: random_post_cost_comparison(random_target, cost_r)
        for name, cost_r in COST_SCENARIOS.items()
    }
    mfe = mfe_breakdown(high_vol_observations)
    flats = flat_trade_breakdown(high_vol_observations)
    decision = b6_decision(post_cost, flats)

    return _json_safe({
        "schema": "setup_b_cost_aware_report_v1",
        "scope": "analysis-only research report over reconstructed B5 validation high-vol subset",
        "validation_target": VALIDATION_TARGET,
        "reconstruction": {
            "expected_n": EXPECTED_HIGH_VOL_N,
            "reconstructed_n": len(high_vol_observations),
            "matched_expected_n": True,
        },
        "raw_validation_high_vol_metrics": raw_target_metrics,
        "post_cost_scenarios": post_cost,
        "random_post_cost_comparison": random_post_cost,
        "mfe_breakdown": mfe,
        "flat_trade_breakdown": flats,
        "b6_decision": decision,
        "interpretation": {
            "cost_handling": "subtract cost_r from each 1.5R trade outcome; preserve original win/loss/flat class counts",
            "random_cost_handling": "subtract the same cost_r from B5 pre-cost random expectancy distribution",
            "time_to_peak_mfe": "not_available_in_b5_observations",
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        },
    })


def post_cost_metrics(
    observations: Sequence[dict[str, object]],
    cost_r: Decimal,
    target: str = VALIDATION_TARGET,
) -> dict[str, object]:
    """Apply round-trip cost in R units to each outcome."""

    raw_values = [_outcome_r(str(obs[f"outcome_{target}"]), target) for obs in observations]
    post_values = [value - cost_r for value in raw_values]
    positive = [value for value in post_values if value > Decimal("0")]
    negative = [value for value in post_values if value < Decimal("0")]
    total = sum(post_values, Decimal("0"))
    profit_factor = _profit_factor(post_values)

    return {
        "n": len(post_values),
        "cost_r": cost_r,
        "post_cost_expectancy_r": _average(post_values),
        "post_cost_total_r": total,
        "post_cost_avg_r": _average(post_values),
        "post_cost_profit_factor": profit_factor,
        "post_cost_positive_count": len(positive),
        "post_cost_negative_count": len(negative),
        "post_cost_nonpositive_count": sum(1 for value in post_values if value <= Decimal("0")),
        "edge_survives_costs": _average(post_values) is not None
        and _average(post_values) > Decimal("0"),
    }


def random_post_cost_comparison(
    random_target_summary: dict[str, object],
    cost_r: Decimal,
) -> dict[str, object]:
    """Subtract the same R cost from B5 random expectancy distribution."""

    expectancy = random_target_summary.get("expectancy_r", {})
    if not isinstance(expectancy, dict):
        expectancy = {}
    adjusted = {
        key: (_optional_decimal(value) - cost_r if _optional_decimal(value) is not None else None)
        for key, value in expectancy.items()
    }
    return {
        "cost_r": cost_r,
        "assumption": "same cost_r subtracted from pre-cost random expectancy distribution",
        "random_median_expectancy_post_cost": adjusted.get("median"),
        "random_p75_expectancy_post_cost": adjusted.get("p75"),
        "random_p90_expectancy_post_cost": adjusted.get("p90"),
        "expectancy_distribution_post_cost": adjusted,
    }


def mfe_breakdown(
    observations: Sequence[dict[str, object]],
    target: str = VALIDATION_TARGET,
) -> dict[str, object]:
    """Summarize MFE shape for the validation high-vol subset."""

    values = _decimal_values(observations, f"mfe_{target}")
    return {
        "n": len(values),
        "avg_mfe_r": _average(values),
        "median_mfe_r": _median(values),
        "p25_mfe_r": _percentile(values, Decimal("0.25")),
        "p75_mfe_r": _percentile(values, Decimal("0.75")),
        "p90_mfe_r": _percentile(values, Decimal("0.90")),
        "pct_reached_0_3r": _pct_at_least(values, Decimal("0.3")),
        "pct_reached_0_5r": _pct_at_least(values, Decimal("0.5")),
        "pct_reached_0_7r": _pct_at_least(values, Decimal("0.7")),
        "pct_reached_1_0r": _pct_at_least(values, Decimal("1.0")),
        "pct_reached_1_5r": _pct_at_least(values, Decimal("1.5")),
        "avg_time_to_peak_mfe_bars": None,
        "median_time_to_peak_mfe_bars": None,
        "time_to_peak_mfe_source": "not_available_in_b5_observations",
    }


def flat_trade_breakdown(
    observations: Sequence[dict[str, object]],
    target: str = VALIDATION_TARGET,
) -> dict[str, object]:
    """Summarize high-vol flat trades for the target."""

    flats = [obs for obs in observations if obs.get(f"outcome_{target}") == "flat"]
    mfe_vals = _decimal_values(flats, f"mfe_{target}")
    classifications = [_classify_flat(obs, target) for obs in flats]
    counts = {
        label: classifications.count(label)
        for label in ("near_win", "dead_flat", "adverse_flat", "ordinary_flat")
    }
    return {
        "flat_count": len(flats),
        "avg_flat_mfe_r": _average(mfe_vals),
        "median_flat_mfe_r": _median(mfe_vals),
        "pct_flat_mfe_ge_0_5r": _pct_at_least(mfe_vals, Decimal("0.5")),
        "pct_flat_mfe_ge_0_7r": _pct_at_least(mfe_vals, Decimal("0.7")),
        "pct_flat_mfe_ge_1_0r": _pct_at_least(mfe_vals, Decimal("1.0")),
        "flat_classification_counts": counts,
        "pct_flat_dead_flat": _rate(counts["dead_flat"], len(flats)),
        "pct_flat_near_win": _rate(counts["near_win"], len(flats)),
    }


def b6_decision(
    post_cost_scenarios: dict[str, dict[str, object]],
    flat_decomp: dict[str, object],
) -> dict[str, object]:
    """Apply the B6 decision gate."""

    expectancies = [
        _optional_decimal(metrics.get("post_cost_expectancy_r"))
        for metrics in post_cost_scenarios.values()
    ]
    negative_all = all(value is not None and value < Decimal("0") for value in expectancies)
    moderate = post_cost_scenarios["moderate"]
    moderate_exp = _optional_decimal(moderate.get("post_cost_expectancy_r"))
    median_flat_mfe = _optional_decimal(flat_decomp.get("median_flat_mfe_r"))
    pct_flat_ge_1r = _optional_decimal(flat_decomp.get("pct_flat_mfe_ge_1_0r"))
    mfe_support = bool(
        (median_flat_mfe is not None and median_flat_mfe >= Decimal("0.7"))
        or (pct_flat_ge_1r is not None and pct_flat_ge_1r >= Decimal("0.30"))
    )
    mfe_opportunity = bool(
        moderate_exp is not None and moderate_exp < Decimal("0") and mfe_support
    )

    if negative_all and not mfe_opportunity:
        decision = B6_RETIRE
    elif negative_all and mfe_opportunity:
        decision = B6_LONG_SHOT
    elif moderate_exp is not None and moderate_exp > Decimal("0") and mfe_support:
        decision = B6_CANDIDATE
    else:
        decision = B6_RETIRE

    return {
        "decision": decision,
        "post_cost_negative_under_all_scenarios": negative_all,
        "mfe_opportunity": mfe_opportunity,
        "mfe_support": mfe_support,
        "moderate_post_cost_expectancy_r": moderate_exp,
        "median_flat_mfe_r": median_flat_mfe,
        "pct_flat_mfe_ge_1_0r": pct_flat_ge_1r,
        "paper_trading_recommended": False,
        "live_trading_recommended": False,
    }


def write_cost_aware_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic B6 artifacts."""

    text_out = Path(text_path)
    json_out = Path(json_path)
    text_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    text_out.write_text(format_cost_aware_report(report), encoding="utf-8")
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_cost_aware_report(report: dict[str, object]) -> str:
    """Format a stable text report."""

    raw = report["raw_validation_high_vol_metrics"]
    decision = report["b6_decision"]
    mfe = report["mfe_breakdown"]
    flats = report["flat_trade_breakdown"]
    lines = [
        "Setup B Stage B6 cost-aware high-volatility report",
        "",
        "Scope: analysis-only research report.",
        "No detector change, parameter change, runtime wiring, paper trading, or live trading.",
        "",
        f"validation_target: {report['validation_target']}",
        f"reconstructed_n: {report['reconstruction']['reconstructed_n']}",
        f"matched_expected_n: {report['reconstruction']['matched_expected_n']}",
        "",
        "Raw validation high-vol metrics",
        f"  n: {raw['n']}",
        f"  wins/losses/flats: {raw['wins']}/{raw['losses']}/{raw['flats']}",
        f"  expectancy_r: {raw['expectancy_r']}",
        f"  profit_factor: {raw['profit_factor']}",
        f"  avg_mfe_r: {raw['avg_mfe_r']}",
        f"  median_mfe_r: {raw['median_mfe_r']}",
        "",
        "Post-cost scenarios",
    ]
    for name, metrics in report["post_cost_scenarios"].items():
        lines.extend([
            f"  {name}: cost_r={metrics['cost_r']}",
            f"    expectancy_r={metrics['post_cost_expectancy_r']}",
            f"    total_r={metrics['post_cost_total_r']}",
            f"    profit_factor={metrics['post_cost_profit_factor']}",
            f"    edge_survives_costs={metrics['edge_survives_costs']}",
        ])
    lines.extend([
        "",
        "Random post-cost comparison",
    ])
    for name, metrics in report["random_post_cost_comparison"].items():
        lines.extend([
            f"  {name}:",
            f"    median_expectancy={metrics['random_median_expectancy_post_cost']}",
            f"    p75_expectancy={metrics['random_p75_expectancy_post_cost']}",
            f"    p90_expectancy={metrics['random_p90_expectancy_post_cost']}",
        ])
    lines.extend([
        "",
        "MFE breakdown",
        f"  avg_mfe_r: {mfe['avg_mfe_r']}",
        f"  median_mfe_r: {mfe['median_mfe_r']}",
        f"  p25/p75/p90: {mfe['p25_mfe_r']} / {mfe['p75_mfe_r']} / {mfe['p90_mfe_r']}",
        f"  pct_reached_0_5r: {mfe['pct_reached_0_5r']}",
        f"  pct_reached_1_0r: {mfe['pct_reached_1_0r']}",
        f"  pct_reached_1_5r: {mfe['pct_reached_1_5r']}",
        "",
        "Flat-trade breakdown",
        f"  flat_count: {flats['flat_count']}",
        f"  avg_flat_mfe_r: {flats['avg_flat_mfe_r']}",
        f"  median_flat_mfe_r: {flats['median_flat_mfe_r']}",
        f"  pct_flat_mfe_ge_0_7r: {flats['pct_flat_mfe_ge_0_7r']}",
        f"  pct_flat_mfe_ge_1_0r: {flats['pct_flat_mfe_ge_1_0r']}",
        f"  classifications: {flats['flat_classification_counts']}",
        "",
        "B6 decision",
        f"  decision: {decision['decision']}",
        f"  mfe_opportunity: {decision['mfe_opportunity']}",
        f"  post_cost_negative_under_all_scenarios: {decision['post_cost_negative_under_all_scenarios']}",
        "",
        "Interpretation",
        "  The B5 validation pass remains real but the raw edge is extremely small.",
        "  Cost-aware evidence does not authorize paper trading or live trading.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def load_json(path: str | Path) -> dict[str, object]:
    """Load a JSON object from disk."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _outcome_r(outcome: str, target: str) -> Decimal:
    if outcome == "win":
        if target == "1_5r":
            return Decimal("1.5")
        if target == "1r":
            return Decimal("1")
        if target == "2r":
            return Decimal("2")
    if outcome == "loss":
        return Decimal("-1")
    return Decimal("0")


def _classify_flat(obs: dict[str, object], target: str) -> str:
    mfe = _optional_decimal(obs.get(f"mfe_{target}")) or Decimal("0")
    mae = _optional_decimal(obs.get(f"mae_{target}")) or Decimal("0")
    if mfe >= Decimal("0.8"):
        return "near_win"
    if abs(mfe) < Decimal("0.3") and abs(mae) < Decimal("0.3"):
        return "dead_flat"
    if mae <= Decimal("-0.8"):
        return "adverse_flat"
    return "ordinary_flat"


def _decimal_values(observations: Sequence[dict[str, object]], key: str) -> list[Decimal]:
    return [
        Decimal(str(obs[key]))
        for obs in observations
        if obs.get(key) is not None
    ]


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
    values_sorted = sorted(values)
    mid = len(values_sorted) // 2
    if len(values_sorted) % 2:
        return values_sorted[mid]
    return (values_sorted[mid - 1] + values_sorted[mid]) / Decimal("2")


def _percentile(values: Sequence[Decimal], percentile: Decimal) -> Decimal | None:
    if not values:
        return None
    values_sorted = sorted(values)
    if len(values_sorted) == 1:
        return values_sorted[0]
    rank = percentile * Decimal(len(values_sorted) - 1)
    lower = int(rank.to_integral_value(rounding="ROUND_FLOOR"))
    upper = int(rank.to_integral_value(rounding="ROUND_CEILING"))
    if lower == upper:
        return values_sorted[lower]
    frac = rank - Decimal(lower)
    return values_sorted[lower] + ((values_sorted[upper] - values_sorted[lower]) * frac)


def _pct_at_least(values: Sequence[Decimal], threshold: Decimal) -> Decimal | None:
    if not values:
        return None
    return Decimal(sum(1 for value in values if value >= threshold)) / Decimal(len(values))


def _rate(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return Decimal(count) / Decimal(total)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
