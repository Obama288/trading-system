"""Conditional random-entry baseline for Setup B candidate tag buckets.

Scope: exploratory research only.
No profitability, paper-trading, live-trading, or readiness claim.

KEY DIFFERENCE from setup_b_random_baseline: random entries are sampled only
from candles satisfying the same tag condition as the Setup B bucket under test.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle
from .indicators import atr as compute_atr
from .setup_b_conditional_diagnostics import ATR_PERIOD, SMA_PERIOD, tag_observations
from .setup_b_random_baseline import (
    BucketSpec,
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    TARGETS,
    TARGET_R_VALUES,
    TIMEOUT_BARS_4H,
)


MEANINGFUL_MARGIN_THRESHOLD = Decimal("0.05")

CONDITION_VOL_HIGH = "volatility_regime=high"
CONDITION_TREND_BELOW_FALLING = "slow_trend_state=below_sma_falling"
CONDITION_INTERSECTION = "volatility_regime=high AND slow_trend_state=below_sma_falling"

CANDIDATE_CONDITIONS = (
    CONDITION_VOL_HIGH,
    CONDITION_TREND_BELOW_FALLING,
    CONDITION_INTERSECTION,
)

_P67 = Decimal("0.667")


def build_eligible_indices(
    candles_by_symbol: dict[str, Sequence[Candle]],
    condition_name: str,
    timeout_bars: int = TIMEOUT_BARS_4H,
) -> dict[str, list[int]]:
    """Return per-symbol candle indices satisfying condition and having sufficient lookahead."""

    if condition_name == CONDITION_VOL_HIGH:
        return _vol_high_eligible(candles_by_symbol, timeout_bars)
    if condition_name == CONDITION_TREND_BELOW_FALLING:
        return _trend_below_falling_eligible(candles_by_symbol, timeout_bars)
    if condition_name == CONDITION_INTERSECTION:
        vol = _vol_high_eligible(candles_by_symbol, timeout_bars)
        trend = _trend_below_falling_eligible(candles_by_symbol, timeout_bars)
        return _intersect_eligible(vol, trend)
    raise ValueError(f"unknown condition: {condition_name!r}")


def build_conditional_bucket_specs(
    tagged_observations: Sequence[dict[str, object]],
    condition_name: str,
) -> list[BucketSpec]:
    """Build BucketSpec list from observations satisfying condition_name."""

    filtered = _filter_by_condition(tagged_observations, condition_name)
    grouped: dict[tuple[str, str], list[Decimal]] = defaultdict(list)
    for obs in filtered:
        symbol = str(obs["symbol"])
        direction = str(obs["signal_direction"])
        entry = Decimal(str(obs["entry_price"]))
        stop = Decimal(str(obs["stop"]))
        risk = abs(entry - stop)
        if risk <= Decimal("0"):
            raise ValueError(f"non-positive risk distance: {symbol} {direction}")
        grouped[(symbol, direction)].append(risk)

    return [
        BucketSpec(
            symbol=symbol,
            direction=direction,
            count=len(risks),
            risk_distances=tuple(risks),
        )
        for (symbol, direction), risks in sorted(grouped.items())
    ]


def run_all_conditional_baselines(
    *,
    observations: Sequence[dict[str, object]],
    candles_by_symbol: dict[str, Sequence[Candle]],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    timeout_bars: int = TIMEOUT_BARS_4H,
) -> dict[str, object]:
    """Run conditional random baseline for all candidate conditions and return combined report."""

    tagged = tag_observations(observations, candles_by_symbol)

    conditions_out: dict[str, object] = {}
    for condition_name in CANDIDATE_CONDITIONS:
        conditions_out[condition_name] = _run_one_condition(
            tagged_observations=tagged,
            candles_by_symbol=candles_by_symbol,
            condition_name=condition_name,
            iterations=iterations,
            seed=seed,
            timeout_bars=timeout_bars,
        )

    return _json_safe(
        {
            "schema": "setup_b_conditional_random_baseline_v1",
            "seed": seed,
            "iterations": iterations,
            "timeout_bars_4h": timeout_bars,
            "conditions": conditions_out,
        }
    )


def write_conditional_baseline_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic conditional random baseline artifacts."""

    text_out = Path(text_path)
    json_out = Path(json_path)
    text_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    text_out.write_text(format_conditional_baseline_report(report), encoding="utf-8")
    json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_conditional_baseline_report(report: dict[str, object]) -> str:
    """Format a stable text report for the conditional random baseline."""

    lines = [
        "Setup B conditional random-entry baseline",
        "",
        "Scope: exploratory research only.",
        "No profitability, paper-trading, live-trading, or readiness claim.",
        "",
        f"seed: {report['seed']}",
        f"iterations: {report['iterations']}",
        f"timeout_bars_4h: {report['timeout_bars_4h']}",
    ]

    conditions = report["conditions"]  # type: ignore[index]
    for cond_name in CANDIDATE_CONDITIONS:
        if cond_name not in conditions:  # type: ignore[operator]
            continue
        cond = conditions[cond_name]  # type: ignore[index]
        lines.extend(["", f"Condition: {cond_name}"])
        lines.append(f"  observation_count: {cond['observation_count']}")  # type: ignore[index]

        if int(cond["observation_count"]) == 0:  # type: ignore[arg-type]
            lines.append(f"  note: {cond.get('note', 'no observations')}")  # type: ignore[union-attr]
            continue

        lines.append("  bucket_distribution:")
        for bucket_key, count in sorted(cond["bucket_distribution"].items()):  # type: ignore[union-attr]
            lines.append(f"    {bucket_key}: {count}")

        lines.append("  eligible_candle_counts:")
        for symbol, count in sorted(cond["eligible_candle_counts"].items()):  # type: ignore[union-attr]
            lines.append(f"    {symbol}: {count}")

        for target in TARGETS:
            actual = cond["setup_b_actual"][target]  # type: ignore[index]
            random_t = cond["conditional_random_baseline"][target]  # type: ignore[index]
            cmp = cond["comparison"][target]  # type: ignore[index]
            lines.extend(
                [
                    f"  target: {target}",
                    f"    setup_b_expectancy_r: {actual['expectancy_r']}",
                    f"    conditional_random_median_expectancy_r: {random_t['expectancy_r']['median']}",
                    f"    conditional_random_p75_expectancy_r: {random_t['expectancy_r']['p75']}",
                    f"    conditional_random_p90_expectancy_r: {random_t['expectancy_r']['p90']}",
                    f"    setup_b_avg_mfe_r: {actual['avg_mfe_r']}",
                    f"    conditional_random_median_avg_mfe_r: {random_t['avg_mfe_r']['median']}",
                    f"    beats_conditional_random_median_expectancy: {cmp['beats_conditional_random_median_expectancy']}",
                    f"    beats_conditional_random_p75_expectancy: {cmp['beats_conditional_random_p75_expectancy']}",
                    f"    beats_conditional_random_p90_expectancy: {cmp['beats_conditional_random_p90_expectancy']}",
                    f"    beats_conditional_random_median_mfe: {cmp['beats_conditional_random_median_mfe']}",
                    f"    meaningful_margin_over_p75: {cmp['meaningful_margin_over_p75']}",
                    f"    meaningful_margin_classification: {cmp['meaningful_margin_classification']}",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def _run_one_condition(
    *,
    tagged_observations: Sequence[dict[str, object]],
    candles_by_symbol: dict[str, Sequence[Candle]],
    condition_name: str,
    iterations: int,
    seed: int,
    timeout_bars: int,
) -> dict[str, object]:
    eligible_indices = build_eligible_indices(candles_by_symbol, condition_name, timeout_bars)
    bucket_specs = build_conditional_bucket_specs(tagged_observations, condition_name)
    observation_count = sum(spec.count for spec in bucket_specs)

    eligible_counts = {sym: len(idx) for sym, idx in sorted(eligible_indices.items())}

    if observation_count == 0:
        return {
            "observation_count": 0,
            "bucket_distribution": {},
            "eligible_candle_counts": eligible_counts,
            "setup_b_actual": {},
            "conditional_random_baseline": {},
            "comparison": {},
            "note": "no observations in this condition bucket",
        }

    for spec in bucket_specs:
        if not eligible_indices.get(spec.symbol):
            raise ValueError(
                f"no eligible candles for {spec.symbol} in condition {condition_name!r}"
            )

    filtered = _filter_by_condition(tagged_observations, condition_name)
    actual_metrics: dict[str, object] = {
        target: _bucket_metrics_for_target(filtered, target) for target in TARGETS
    }

    rng = random.Random(seed)
    iteration_metrics: list[dict[str, dict[str, object]]] = []
    for _ in range(iterations):
        entries = _sample_conditional_iteration(
            bucket_specs=bucket_specs,
            eligible_indices=eligible_indices,
            candles_by_symbol=candles_by_symbol,
            rng=rng,
            timeout_bars=timeout_bars,
        )
        iteration_metrics.append(_metrics_for_iteration(entries))

    random_summary = _summarize_iteration_metrics(iteration_metrics)
    comparison = _compare_actual_to_conditional_random(actual_metrics, random_summary)

    return {
        "observation_count": observation_count,
        "bucket_distribution": {
            f"{spec.symbol} / {spec.direction}": spec.count for spec in bucket_specs
        },
        "eligible_candle_counts": eligible_counts,
        "setup_b_actual": actual_metrics,
        "conditional_random_baseline": random_summary,
        "comparison": comparison,
    }


def _filter_by_condition(
    tagged_observations: Sequence[dict[str, object]],
    condition_name: str,
) -> list[dict[str, object]]:
    if condition_name == CONDITION_VOL_HIGH:
        return [obs for obs in tagged_observations if obs.get("tag_volatility_regime") == "high"]
    if condition_name == CONDITION_TREND_BELOW_FALLING:
        return [
            obs for obs in tagged_observations
            if obs.get("tag_slow_trend_state") == "below_sma_falling"
        ]
    if condition_name == CONDITION_INTERSECTION:
        return [
            obs for obs in tagged_observations
            if obs.get("tag_volatility_regime") == "high"
            and obs.get("tag_slow_trend_state") == "below_sma_falling"
        ]
    raise ValueError(f"unknown condition: {condition_name!r}")


# ---------------------------------------------------------------------------
# Eligible index builders
# ---------------------------------------------------------------------------


def _vol_high_eligible(
    candles_by_symbol: dict[str, Sequence[Candle]],
    timeout_bars: int,
) -> dict[str, list[int]]:
    atr_by_symbol = {sym: compute_atr(c, ATR_PERIOD) for sym, c in candles_by_symbol.items()}

    p67_by_symbol: dict[str, Decimal] = {}
    for sym, series in atr_by_symbol.items():
        valid = sorted(v for v in series if v is not None)
        if len(valid) < 3:
            continue
        p67_by_symbol[sym] = _percentile_value(valid, _P67)

    eligible: dict[str, list[int]] = {}
    for sym, candles in candles_by_symbol.items():
        series = atr_by_symbol[sym]
        p67 = p67_by_symbol.get(sym)
        max_idx = len(candles) - timeout_bars - 1
        if p67 is None or max_idx < 0:
            eligible[sym] = []
            continue
        eligible[sym] = [
            i for i, val in enumerate(series)
            if val is not None and val >= p67 and i <= max_idx
        ]
    return eligible


def _trend_below_falling_eligible(
    candles_by_symbol: dict[str, Sequence[Candle]],
    timeout_bars: int,
) -> dict[str, list[int]]:
    eligible: dict[str, list[int]] = {}
    for sym, candles in candles_by_symbol.items():
        sma = _compute_sma(candles, SMA_PERIOD)
        max_idx = len(candles) - timeout_bars - 1
        indices: list[int] = []
        for i in range(1, len(candles)):
            if i > max_idx:
                break
            sma_now = sma[i]
            sma_prev = sma[i - 1]
            if sma_now is None or sma_prev is None:
                continue
            if candles[i].close < sma_now and sma_now < sma_prev:
                indices.append(i)
        eligible[sym] = indices
    return eligible


def _intersect_eligible(
    eligible_a: dict[str, list[int]],
    eligible_b: dict[str, list[int]],
) -> dict[str, list[int]]:
    all_symbols = set(eligible_a) | set(eligible_b)
    return {
        sym: sorted(set(eligible_a.get(sym, [])) & set(eligible_b.get(sym, [])))
        for sym in all_symbols
    }


def _compute_sma(candles: Sequence[Candle], period: int) -> list[Decimal | None]:
    result: list[Decimal | None] = [None] * len(candles)
    for i in range(period - 1, len(candles)):
        window_sum = sum(
            (candles[j].close for j in range(i - period + 1, i + 1)),
            Decimal("0"),
        )
        result[i] = window_sum / Decimal(period)
    return result


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


def _sample_conditional_iteration(
    *,
    bucket_specs: Sequence[BucketSpec],
    eligible_indices: dict[str, list[int]],
    candles_by_symbol: dict[str, Sequence[Candle]],
    rng: random.Random,
    timeout_bars: int,
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for spec in bucket_specs:
        candles = candles_by_symbol[spec.symbol]
        eligible = eligible_indices[spec.symbol]
        for _ in range(spec.count):
            entry_index = rng.choice(eligible)
            risk = rng.choice(spec.risk_distances)
            entries.append(
                _evaluate_entry(
                    candles=candles,
                    entry_index=entry_index,
                    direction=spec.direction,
                    risk_distance=risk,
                    timeout_bars=timeout_bars,
                )
            )
    return entries


def _evaluate_entry(
    *,
    candles: Sequence[Candle],
    entry_index: int,
    direction: str,
    risk_distance: Decimal,
    timeout_bars: int,
) -> dict[str, object]:
    entry = candles[entry_index].close
    if direction == "long":
        stop = entry - risk_distance
    elif direction == "short":
        stop = entry + risk_distance
    else:
        raise ValueError(f"unsupported direction: {direction}")

    window = candles[entry_index + 1 : entry_index + 1 + timeout_bars]
    result: dict[str, object] = {
        "direction": direction,
        "entry_price": entry,
        "stop": stop,
        "risk_distance": risk_distance,
    }
    for target, target_r in TARGET_R_VALUES.items():
        target_price = _target_price(entry, risk_distance, target_r, direction)
        outcome, mae_r, mfe_r, bars = _resolve_outcome(
            window=window,
            entry=entry,
            stop=stop,
            target=target_price,
            direction=direction,
            risk_distance=risk_distance,
        )
        result[f"outcome_{target}"] = outcome
        result[f"mae_{target}"] = mae_r
        result[f"mfe_{target}"] = mfe_r
        result[f"bars_to_resolution_{target}"] = bars
    return result


def _target_price(
    entry: Decimal, risk_distance: Decimal, target_r: Decimal, direction: str
) -> Decimal:
    if direction == "long":
        return entry + (risk_distance * target_r)
    return entry - (risk_distance * target_r)


def _resolve_outcome(
    *,
    window: Sequence[Candle],
    entry: Decimal,
    stop: Decimal,
    target: Decimal,
    direction: str,
    risk_distance: Decimal,
) -> tuple[str, Decimal, Decimal, int]:
    if not window:
        return "flat", Decimal("0"), Decimal("0"), 0

    for offset, candle in enumerate(window, start=1):
        resolution_window = window[:offset]
        if direction == "long":
            if candle.low <= stop:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "loss", mae_r, mfe_r, offset
            if candle.high >= target:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "win", mae_r, mfe_r, offset
        else:
            if candle.high >= stop:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "loss", mae_r, mfe_r, offset
            if candle.low <= target:
                mae_r, mfe_r = _excursions(
                    resolution_window, entry=entry, risk_distance=risk_distance, direction=direction
                )
                return "win", mae_r, mfe_r, offset

    mae_r, mfe_r = _excursions(window, entry=entry, risk_distance=risk_distance, direction=direction)
    return "flat", mae_r, mfe_r, len(window)


def _excursions(
    window: Sequence[Candle],
    *,
    entry: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> tuple[Decimal, Decimal]:
    if direction == "long":
        mfe_r = max((c.high - entry) / risk_distance for c in window)
        mae_r = min((c.low - entry) / risk_distance for c in window)
    else:
        mfe_r = max((entry - c.low) / risk_distance for c in window)
        mae_r = min((entry - c.high) / risk_distance for c in window)
    return mae_r, mfe_r


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------


def _metrics_for_iteration(
    entries: Sequence[dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {target: _target_metrics(entries, target) for target in TARGETS}


def _target_metrics(
    entries: Sequence[dict[str, object]], target: str
) -> dict[str, object]:
    target_r = TARGET_R_VALUES[target]
    outcomes = [str(e[f"outcome_{target}"]) for e in entries]
    r_values = [_outcome_r(o, target_r) for o in outcomes]
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    flats = outcomes.count("flat")
    mae_vals = [Decimal(str(e[f"mae_{target}"])) for e in entries]
    mfe_vals = [Decimal(str(e[f"mfe_{target}"])) for e in entries]
    n = len(entries)
    return {
        "observations": n,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": _rate(wins, n),
        "expectancy_r": _average(r_values),
        "avg_mae_r": _average(mae_vals),
        "avg_mfe_r": _average(mfe_vals),
    }


def _bucket_metrics_for_target(
    observations: Sequence[dict[str, object]], target: str
) -> dict[str, object]:
    target_r = TARGET_R_VALUES[target]
    outcomes = [str(obs[f"outcome_{target}"]) for obs in observations]
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    flats = outcomes.count("flat")
    n = len(observations)
    r_values = [_outcome_r(o, target_r) for o in outcomes]
    mae_vals = [
        Decimal(str(obs[f"mae_{target}"]))
        for obs in observations
        if obs.get(f"mae_{target}") is not None
    ]
    mfe_vals = [
        Decimal(str(obs[f"mfe_{target}"]))
        for obs in observations
        if obs.get(f"mfe_{target}") is not None
    ]
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": _rate(wins, n),
        "flat_rate": _rate(flats, n),
        "expectancy_r": _average(r_values),
        "avg_mae_r": _average(mae_vals),
        "avg_mfe_r": _average(mfe_vals),
        "median_mae_r": _median(mae_vals),
        "median_mfe_r": _median(mfe_vals),
    }


def _summarize_iteration_metrics(
    iteration_metrics: Sequence[dict[str, dict[str, object]]],
) -> dict[str, object]:
    output: dict[str, object] = {}
    for target in TARGETS:
        output[target] = {
            metric: _distribution_summary(
                [
                    _optional_decimal(iteration[target][metric])
                    for iteration in iteration_metrics
                    if _optional_decimal(iteration[target][metric]) is not None
                ]
            )
            for metric in ("expectancy_r", "win_rate", "avg_mae_r", "avg_mfe_r")
        }
    return output


def _compare_actual_to_conditional_random(
    actual_metrics: dict[str, object],
    random_summary: dict[str, object],
) -> dict[str, object]:
    output: dict[str, object] = {}
    for target in TARGETS:
        actual = actual_metrics[target]  # type: ignore[index]
        random_t = random_summary[target]  # type: ignore[index]

        raw_exp = actual.get("expectancy_r")  # type: ignore[union-attr]
        actual_exp = Decimal(str(raw_exp)) if raw_exp is not None else Decimal("0")
        raw_mfe = actual.get("avg_mfe_r")  # type: ignore[union-attr]
        actual_mfe = Decimal(str(raw_mfe)) if raw_mfe is not None else Decimal("0")

        exp_dist = random_t["expectancy_r"]  # type: ignore[index]
        mfe_dist = random_t["avg_mfe_r"]  # type: ignore[index]

        median_exp = _optional_decimal(exp_dist["median"])  # type: ignore[index]
        p75_exp = _optional_decimal(exp_dist["p75"])  # type: ignore[index]
        p90_exp = _optional_decimal(exp_dist["p90"])  # type: ignore[index]
        median_mfe = _optional_decimal(mfe_dist["median"])  # type: ignore[index]

        margin_over_p75 = (actual_exp - p75_exp) if p75_exp is not None else None
        if margin_over_p75 is not None:
            classification: str | None = (
                "potentially_meaningful"
                if margin_over_p75 >= MEANINGFUL_MARGIN_THRESHOLD
                else "weak"
            )
        else:
            classification = None

        output[target] = {
            "beats_conditional_random_median_expectancy": (
                median_exp is not None and actual_exp > median_exp
            ),
            "beats_conditional_random_p75_expectancy": (
                p75_exp is not None and actual_exp > p75_exp
            ),
            "beats_conditional_random_p90_expectancy": (
                p90_exp is not None and actual_exp > p90_exp
            ),
            "beats_conditional_random_median_mfe": (
                median_mfe is not None and actual_mfe > median_mfe
            ),
            "meaningful_margin_over_p75": str(margin_over_p75) if margin_over_p75 is not None else None,
            "meaningful_margin_classification": classification,
        }
    return output


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


def _percentile_value(sorted_values: list[Decimal], percentile: Decimal) -> Decimal:
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = percentile * Decimal(len(sorted_values) - 1)
    lower = int(rank.to_integral_value(rounding="ROUND_FLOOR"))
    upper = int(rank.to_integral_value(rounding="ROUND_CEILING"))
    if lower == upper:
        return sorted_values[lower]
    frac = rank - Decimal(lower)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * frac


def _distribution_summary(values: Sequence[Decimal]) -> dict[str, Decimal | None]:
    if not values:
        return {
            "mean": None,
            "median": None,
            "p10": None,
            "p25": None,
            "p75": None,
            "p90": None,
            "min": None,
            "max": None,
        }
    sv = sorted(values)
    return {
        "mean": _average(sv),
        "median": _median(sv),
        "p10": _percentile_value(sv, Decimal("0.10")),
        "p25": _percentile_value(sv, Decimal("0.25")),
        "p75": _percentile_value(sv, Decimal("0.75")),
        "p90": _percentile_value(sv, Decimal("0.90")),
        "min": sv[0],
        "max": sv[-1],
    }


def _average(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, Decimal("0")) / Decimal(len(values))


def _median(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    sv = sorted(values)
    mid = len(sv) // 2
    if len(sv) % 2:
        return sv[mid]
    return (sv[mid - 1] + sv[mid]) / Decimal("2")


def _rate(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return Decimal(count) / Decimal(total)


def _outcome_r(outcome: str, target_r: Decimal) -> Decimal:
    if outcome == "win":
        return target_r
    if outcome == "loss":
        return Decimal("-1")
    return Decimal("0")


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
