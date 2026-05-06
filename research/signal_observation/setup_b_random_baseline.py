"""Random-entry baseline for Setup B signal-quality analysis."""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Sequence

from research.signal_observation.candles import Candle
from research.signal_observation.csv_loader import load_ohlcv_csv


TARGETS = ("1r", "1_5r", "2r")
TARGET_R_VALUES = {
    "1r": Decimal("1"),
    "1_5r": Decimal("1.5"),
    "2r": Decimal("2"),
}
DEFAULT_SEED = 5403
DEFAULT_ITERATIONS = 1000
TIMEOUT_BARS_4H = 10


@dataclass(frozen=True, slots=True)
class BucketSpec:
    """Random baseline sampling requirements for one symbol/direction bucket."""

    symbol: str
    direction: str
    count: int
    risk_distances: tuple[Decimal, ...]


@dataclass(frozen=True, slots=True)
class RandomOutcome:
    """Outcome for one random entry and one target."""

    outcome: str
    mae_r: Decimal
    mfe_r: Decimal
    bars_to_resolution: int


def load_json(path: str | Path) -> object:
    """Load a local JSON artifact."""

    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_bitget_4h_candles(data_dir: str | Path) -> dict[str, list[Candle]]:
    """Load existing local Bitget 4H CSV candles by symbol."""

    base = Path(data_dir)
    output: dict[str, list[Candle]] = {}
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        path = base / f"{symbol}_USDT-FUTURES_4H.csv"
        output[symbol] = load_ohlcv_csv(path)
    return output


def build_bucket_specs(observations: Sequence[dict[str, object]]) -> list[BucketSpec]:
    """Build symbol/direction/count/risk buckets from actual Setup B observations."""

    grouped: dict[tuple[str, str], list[Decimal]] = defaultdict(list)
    for item in observations:
        symbol = str(item["symbol"])
        direction = str(item["signal_direction"])
        entry = Decimal(str(item["entry_price"]))
        stop = Decimal(str(item["stop"]))
        risk = abs(entry - stop)
        if risk <= Decimal("0"):
            raise ValueError(f"non-positive risk distance for {symbol} {direction}")
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


def run_random_baseline_iterations(
    *,
    observations: Sequence[dict[str, object]],
    candles_by_symbol: dict[str, Sequence[Candle]],
    setup_b_metrics: dict[str, object],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    timeout_bars: int = TIMEOUT_BARS_4H,
) -> dict[str, object]:
    """Run deterministic random-entry baseline iterations."""

    if iterations <= 0:
        raise ValueError("iterations must be greater than zero")
    if timeout_bars <= 0:
        raise ValueError("timeout_bars must be greater than zero")

    bucket_specs = build_bucket_specs(observations)
    rng = random.Random(seed)
    iteration_metrics: list[dict[str, dict[str, object]]] = []
    for _ in range(iterations):
        random_entries = _sample_iteration_entries(
            bucket_specs=bucket_specs,
            candles_by_symbol=candles_by_symbol,
            rng=rng,
            timeout_bars=timeout_bars,
        )
        iteration_metrics.append(_metrics_by_target(random_entries))

    random_summary = _summarize_iterations(iteration_metrics)
    comparisons = _compare_setup_b_to_random(setup_b_metrics, random_summary)
    return _json_safe(
        {
            "schema": "setup_b_random_baseline_v1",
            "seed": seed,
            "iterations": iterations,
            "timeout_bars_4h": timeout_bars,
            "bucket_distribution": {
                f"{spec.symbol} / {spec.direction}": spec.count for spec in bucket_specs
            },
            "setup_b_actual": setup_b_metrics["overall"]["all"],
            "random_baseline": random_summary,
            "comparison": comparisons,
        }
    )


def write_random_baseline_artifacts(
    analysis: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic random-baseline artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_random_baseline_report(analysis), encoding="utf-8")
    json_output.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_random_baseline_report(analysis: dict[str, object]) -> str:
    """Format a stable text report for the random-entry baseline."""

    lines = [
        "Setup B random-entry baseline",
        "",
        "Scope: exploratory research baseline only.",
        "No profitability, paper-trading, live-trading, or readiness claim.",
        "",
        f"seed: {analysis['seed']}",
        f"iterations: {analysis['iterations']}",
        f"timeout_bars_4h: {analysis['timeout_bars_4h']}",
        "",
        "Bucket distribution",
    ]
    for bucket, count in sorted(analysis["bucket_distribution"].items()):  # type: ignore[union-attr]
        lines.append(f"- {bucket}: {count}")

    lines.extend(["", "Setup B vs random baseline"])
    for target in TARGETS:
        actual = analysis["setup_b_actual"][target]  # type: ignore[index]
        random_target = analysis["random_baseline"][target]  # type: ignore[index]
        comparison = analysis["comparison"][target]  # type: ignore[index]
        lines.extend(
            [
                f"target: {target}",
                f"  setup_b_expectancy_r: {actual['expectancy_r']}",
                f"  random_median_expectancy_r: {random_target['expectancy_r']['median']}",
                f"  random_p75_expectancy_r: {random_target['expectancy_r']['p75']}",
                f"  random_p90_expectancy_r: {random_target['expectancy_r']['p90']}",
                f"  setup_b_win_rate: {actual['win_rate']}",
                f"  random_median_win_rate: {random_target['win_rate']['median']}",
                f"  setup_b_flat_rate: {actual['flat_rate']}",
                f"  random_median_flat_rate: {random_target['flat_rate']['median']}",
                f"  setup_b_avg_mae_r: {actual['avg_mae_r']}",
                f"  random_median_avg_mae_r: {random_target['avg_mae_r']['median']}",
                f"  setup_b_avg_mfe_r: {actual['avg_mfe_r']}",
                f"  random_median_avg_mfe_r: {random_target['avg_mfe_r']['median']}",
                f"  beats_random_median_expectancy: {comparison['setup_b_beats_random_median_expectancy']}",
                f"  beats_random_p75_expectancy: {comparison['setup_b_beats_random_p75_expectancy']}",
                f"  beats_random_p90_expectancy: {comparison['setup_b_beats_random_p90_expectancy']}",
                f"  beats_random_median_mfe: {comparison['setup_b_beats_random_median_mfe']}",
                f"  flat_rate_better_than_random_median: {comparison['setup_b_flat_rate_better_than_random_median']}",
                f"  inconclusive: {comparison['random_baseline_inconclusive']}",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _sample_iteration_entries(
    *,
    bucket_specs: Sequence[BucketSpec],
    candles_by_symbol: dict[str, Sequence[Candle]],
    rng: random.Random,
    timeout_bars: int,
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for spec in bucket_specs:
        candles = candles_by_symbol[spec.symbol]
        max_entry_index = len(candles) - timeout_bars - 1
        if max_entry_index < 0:
            raise ValueError(f"not enough future candles for {spec.symbol}")
        for _ in range(spec.count):
            entry_index = rng.randint(0, max_entry_index)
            risk = rng.choice(spec.risk_distances)
            entries.append(
                _evaluate_random_entry(
                    candles=candles,
                    entry_index=entry_index,
                    direction=spec.direction,
                    risk_distance=risk,
                    timeout_bars=timeout_bars,
                )
            )
    return entries


def _evaluate_random_entry(
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
    output: dict[str, object] = {
        "direction": direction,
        "entry_price": entry,
        "stop": stop,
        "risk_distance": risk_distance,
    }
    for target, target_r in TARGET_R_VALUES.items():
        target_price = _target_price(entry, risk_distance, target_r, direction)
        outcome = _resolve_target_outcome(
            window=window,
            entry=entry,
            stop=stop,
            target=target_price,
            target_r=target_r,
            risk_distance=risk_distance,
            direction=direction,
        )
        output[f"outcome_{target}"] = outcome.outcome
        output[f"mae_{target}"] = outcome.mae_r
        output[f"mfe_{target}"] = outcome.mfe_r
        output[f"bars_to_resolution_{target}"] = outcome.bars_to_resolution
    return output


def _resolve_target_outcome(
    *,
    window: Sequence[Candle],
    entry: Decimal,
    stop: Decimal,
    target: Decimal,
    target_r: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> RandomOutcome:
    if not window:
        return RandomOutcome("flat", Decimal("0"), Decimal("0"), 0)

    for offset, candle in enumerate(window, start=1):
        resolution_window = window[:offset]
        if direction == "long":
            if candle.low <= stop:
                mae_r, mfe_r = _excursions_for_window(
                    resolution_window,
                    entry=entry,
                    risk_distance=risk_distance,
                    direction=direction,
                )
                return RandomOutcome("loss", mae_r, mfe_r, offset)
            if candle.high >= target:
                mae_r, mfe_r = _excursions_for_window(
                    resolution_window,
                    entry=entry,
                    risk_distance=risk_distance,
                    direction=direction,
                )
                return RandomOutcome("win", mae_r, mfe_r, offset)
        else:
            if candle.high >= stop:
                mae_r, mfe_r = _excursions_for_window(
                    resolution_window,
                    entry=entry,
                    risk_distance=risk_distance,
                    direction=direction,
                )
                return RandomOutcome("loss", mae_r, mfe_r, offset)
            if candle.low <= target:
                mae_r, mfe_r = _excursions_for_window(
                    resolution_window,
                    entry=entry,
                    risk_distance=risk_distance,
                    direction=direction,
                )
                return RandomOutcome("win", mae_r, mfe_r, offset)

    mae_r, mfe_r = _excursions_for_window(
        window,
        entry=entry,
        risk_distance=risk_distance,
        direction=direction,
    )
    return RandomOutcome("flat", mae_r, mfe_r, len(window))


def _metrics_by_target(entries: Sequence[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {target: _target_metrics(entries, target) for target in TARGETS}


def _target_metrics(entries: Sequence[dict[str, object]], target: str) -> dict[str, object]:
    target_r = TARGET_R_VALUES[target]
    outcomes = [str(item[f"outcome_{target}"]) for item in entries]
    r_values = [_outcome_r(outcome, target_r) for outcome in outcomes]
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    flats = outcomes.count("flat")
    mae_values = [Decimal(str(item[f"mae_{target}"])) for item in entries]
    mfe_values = [Decimal(str(item[f"mfe_{target}"])) for item in entries]
    bars = [Decimal(str(item[f"bars_to_resolution_{target}"])) for item in entries]
    count = len(entries)
    return {
        "observations": count,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": _rate(wins, count),
        "flat_rate": _rate(flats, count),
        "expectancy_r": _average(r_values),
        "profit_factor": _profit_factor(r_values),
        "avg_mae_r": _average(mae_values),
        "avg_mfe_r": _average(mfe_values),
        "median_mae_r": _median(mae_values),
        "median_mfe_r": _median(mfe_values),
        "avg_bars_to_resolution": _average(bars),
        "median_bars_to_resolution": _median(bars),
    }


def _summarize_iterations(
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
            for metric in (
                "expectancy_r",
                "win_rate",
                "flat_rate",
                "avg_mae_r",
                "avg_mfe_r",
            )
        }
    return output


def _compare_setup_b_to_random(
    setup_b_metrics: dict[str, object],
    random_summary: dict[str, object],
) -> dict[str, object]:
    output: dict[str, object] = {}
    setup_actual = setup_b_metrics["overall"]["all"]  # type: ignore[index]
    for target in TARGETS:
        actual = setup_actual[target]  # type: ignore[index]
        random_target = random_summary[target]  # type: ignore[index]
        actual_expectancy = Decimal(str(actual["expectancy_r"]))
        actual_mfe = Decimal(str(actual["avg_mfe_r"]))
        actual_flat_rate = Decimal(str(actual["flat_rate"]))
        median_expectancy = Decimal(str(random_target["expectancy_r"]["median"]))
        p75_expectancy = Decimal(str(random_target["expectancy_r"]["p75"]))
        p90_expectancy = Decimal(str(random_target["expectancy_r"]["p90"]))
        median_mfe = Decimal(str(random_target["avg_mfe_r"]["median"]))
        median_flat_rate = Decimal(str(random_target["flat_rate"]["median"]))
        output[target] = {
            "setup_b_beats_random_median_expectancy": actual_expectancy > median_expectancy,
            "setup_b_beats_random_p75_expectancy": actual_expectancy > p75_expectancy,
            "setup_b_beats_random_p90_expectancy": actual_expectancy > p90_expectancy,
            "setup_b_beats_random_median_mfe": actual_mfe > median_mfe,
            "setup_b_flat_rate_better_than_random_median": actual_flat_rate < median_flat_rate,
            "random_baseline_inconclusive": True,
        }
    return output


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
    sorted_values = sorted(values)
    return {
        "mean": _average(sorted_values),
        "median": _median(sorted_values),
        "p10": _percentile(sorted_values, Decimal("0.10")),
        "p25": _percentile(sorted_values, Decimal("0.25")),
        "p75": _percentile(sorted_values, Decimal("0.75")),
        "p90": _percentile(sorted_values, Decimal("0.90")),
        "min": sorted_values[0],
        "max": sorted_values[-1],
    }


def _percentile(values: Sequence[Decimal], percentile: Decimal) -> Decimal:
    if len(values) == 1:
        return values[0]
    rank = percentile * Decimal(len(values) - 1)
    lower = int(rank.to_integral_value(rounding="ROUND_FLOOR"))
    upper = int(rank.to_integral_value(rounding="ROUND_CEILING"))
    if lower == upper:
        return values[lower]
    fraction = rank - Decimal(lower)
    return values[lower] + ((values[upper] - values[lower]) * fraction)


def _target_price(
    entry: Decimal,
    risk_distance: Decimal,
    target_r: Decimal,
    direction: str,
) -> Decimal:
    if direction == "long":
        return entry + (risk_distance * target_r)
    return entry - (risk_distance * target_r)


def _excursions_for_window(
    window: Sequence[Candle],
    *,
    entry: Decimal,
    risk_distance: Decimal,
    direction: str,
) -> tuple[Decimal, Decimal]:
    if direction == "long":
        mfe_r = max((candle.high - entry) / risk_distance for candle in window)
        mae_r = min((candle.low - entry) / risk_distance for candle in window)
    else:
        mfe_r = max((entry - candle.low) / risk_distance for candle in window)
        mae_r = min((entry - candle.high) / risk_distance for candle in window)
    return mae_r, mfe_r


def _outcome_r(outcome: str, target_r: Decimal) -> Decimal:
    if outcome == "win":
        return target_r
    if outcome == "loss":
        return Decimal("-1")
    return Decimal("0")


def _rate(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return Decimal(count) / Decimal(total)


def _average(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values) / Decimal(len(values))


def _median(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / Decimal("2")


def _profit_factor(values: Sequence[Decimal]) -> Decimal | None:
    wins = sum(value for value in values if value > Decimal("0"))
    losses = abs(sum(value for value in values if value < Decimal("0")))
    if wins == Decimal("0") or losses == Decimal("0"):
        return None
    return wins / losses


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


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
