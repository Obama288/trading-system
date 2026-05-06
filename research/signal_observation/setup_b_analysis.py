"""Setup B signal-quality metrics analysis over local JSON artifacts."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Sequence


TARGETS = ("1r", "1_5r", "2r")
TARGET_R_VALUES = {
    "1r": Decimal("1"),
    "1_5r": Decimal("1.5"),
    "2r": Decimal("2"),
}
@dataclass(frozen=True, slots=True)
class TargetMetrics:
    """Metrics for one observation group and one target."""

    observations: int
    resolved: int
    wins: int
    losses: int
    flats: int
    win_rate: Decimal | None
    loss_rate: Decimal | None
    flat_rate: Decimal | None
    expectancy_r: Decimal | None
    profit_factor: Decimal | None
    avg_win_r: Decimal | None
    avg_loss_r: Decimal | None
    avg_mae_r: Decimal | None
    avg_mfe_r: Decimal | None
    median_mae_r: Decimal | None
    median_mfe_r: Decimal | None
    avg_bars_to_resolution: Decimal | None
    median_bars_to_resolution: Decimal | None
    max_consecutive_losses: int


def load_observations(path: str | Path) -> list[dict[str, object]]:
    """Load observations from a local Setup B JSON artifact."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Setup B observations artifact must contain a list")
    return sorted(
        data,
        key=lambda item: (
            str(item.get("signal_time", "")),
            str(item.get("symbol", "")),
            str(item.get("signal_direction", "")),
        ),
    )


def analyze_setup_b_observations(observations: Sequence[dict[str, object]]) -> dict[str, object]:
    """Build deterministic Setup B metrics analysis."""

    sorted_observations = sorted(
        observations,
        key=lambda item: (
            str(item.get("signal_time", "")),
            str(item.get("symbol", "")),
            str(item.get("signal_direction", "")),
        ),
    )
    analysis = {
        "schema": "setup_b_metrics_analysis_v1",
        "observation_count": len(sorted_observations),
        "overall": _metrics_for_groups({"all": sorted_observations}),
        "by_symbol": _metrics_for_groups(_group_by(sorted_observations, ("symbol",))),
        "by_direction": _metrics_for_groups(_group_by(sorted_observations, ("signal_direction",))),
        "by_symbol_direction": _metrics_for_groups(
            _group_by(sorted_observations, ("symbol", "signal_direction"))
        ),
        "distribution_diagnostics": _distribution_diagnostics(sorted_observations),
        "timing_diagnostics": _timing_diagnostics(sorted_observations),
        "warning_flags": _warning_flags(sorted_observations),
    }
    return _json_safe(analysis)


def write_analysis_artifacts(
    analysis: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic text and JSON analysis artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_analysis_report(analysis), encoding="utf-8")
    json_output.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_analysis_report(analysis: dict[str, object]) -> str:
    """Format a stable text report for Setup B analysis."""

    lines = [
        "Setup B metrics analysis",
        "",
        "Scope: exploratory signal-quality diagnostics only.",
        "No profitability, paper-trading, live-trading, or readiness claim.",
        "",
        f"observations: {analysis['observation_count']}",
        "",
        "Overall by target",
    ]
    overall = analysis["overall"]["all"]  # type: ignore[index]
    for target in TARGETS:
        lines.extend(_format_metric_lines(target, overall[target]))  # type: ignore[index]

    lines.extend(["", "By symbol + direction"])
    by_pair = analysis["by_symbol_direction"]  # type: ignore[assignment]
    for key in sorted(by_pair):
        lines.append(f"group: {key}")
        for target in TARGETS:
            metrics = by_pair[key][target]
            compact = (
                f"  {target}: obs={metrics['observations']} "
                f"W/L/F={metrics['wins']}/{metrics['losses']}/{metrics['flats']} "
                f"expectancy_r={metrics['expectancy_r']} "
                f"profit_factor={metrics['profit_factor']} "
                f"flat_rate={metrics['flat_rate']}"
            )
            lines.append(compact)

    lines.extend(["", "Warning flags"])
    for warning in analysis["warning_flags"]:  # type: ignore[index]
        lines.append(f"- {warning}")
    return "\n".join(lines).rstrip() + "\n"


def summarize_best_worst_pairs(analysis: dict[str, object], target: str) -> tuple[str, str]:
    """Return best and worst symbol-direction groups by expectancy for a target."""

    pairs = analysis["by_symbol_direction"]  # type: ignore[assignment]
    ranked = sorted(
        (
            (Decimal(str(metrics[target]["expectancy_r"])), key)
            for key, metrics in pairs.items()
            if metrics[target]["expectancy_r"] is not None
        ),
        key=lambda item: (item[0], item[1]),
    )
    if not ranked:
        return "none", "none"
    return ranked[-1][1], ranked[0][1]


def _metrics_for_groups(groups: dict[str, Sequence[dict[str, object]]]) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    for group_name in sorted(groups):
        output[group_name] = {
            target: _target_metrics(groups[group_name], target)
            for target in TARGETS
        }
    return output


def _target_metrics(observations: Sequence[dict[str, object]], target: str) -> dict[str, object]:
    target_r = TARGET_R_VALUES[target]
    outcomes = [str(item[f"outcome_{target}"]) for item in observations]
    r_values = [_outcome_r(outcome, target_r) for outcome in outcomes]
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    flats = outcomes.count("flat")
    bars = [_optional_decimal(item.get(f"bars_to_resolution_{target}")) for item in observations]
    bars = [item for item in bars if item is not None]
    mae_values = [_optional_decimal(item.get(f"mae_{target}")) for item in observations]
    mfe_values = [_optional_decimal(item.get(f"mfe_{target}")) for item in observations]
    mae_values = [item for item in mae_values if item is not None]
    mfe_values = [item for item in mfe_values if item is not None]

    count = len(observations)
    resolved = sum(1 for item in observations if item.get(f"bars_to_resolution_{target}") is not None)
    return _json_safe(
        TargetMetrics(
            observations=count,
            resolved=resolved,
            wins=wins,
            losses=losses,
            flats=flats,
            win_rate=_rate(wins, count),
            loss_rate=_rate(losses, count),
            flat_rate=_rate(flats, count),
            expectancy_r=_average(r_values),
            profit_factor=_profit_factor(r_values),
            avg_win_r=_average([value for value in r_values if value > Decimal("0")]),
            avg_loss_r=_average([value for value in r_values if value < Decimal("0")]),
            avg_mae_r=_average(mae_values),
            avg_mfe_r=_average(mfe_values),
            median_mae_r=_median(mae_values),
            median_mfe_r=_median(mfe_values),
            avg_bars_to_resolution=_average(bars),
            median_bars_to_resolution=_median(bars),
            max_consecutive_losses=_max_consecutive_losses(observations, target),
        )
    )


def _distribution_diagnostics(observations: Sequence[dict[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for target in TARGETS:
        outcomes = Counter(str(item[f"outcome_{target}"]) for item in observations)
        output[target] = {
            "r_outcome_counts": dict(sorted(outcomes.items())),
            "mae_buckets": _mae_buckets(
                [_optional_decimal(item.get(f"mae_{target}")) for item in observations]
            ),
            "mfe_buckets": _mfe_buckets(
                [_optional_decimal(item.get(f"mfe_{target}")) for item in observations]
            ),
        }
    return output


def _timing_diagnostics(observations: Sequence[dict[str, object]]) -> dict[str, object]:
    hours = Counter(int(item["signal_hour_utc"]) for item in observations)
    target_stats: dict[str, object] = {}
    for target in TARGETS:
        bars = [_optional_decimal(item.get(f"bars_to_resolution_{target}")) for item in observations]
        bars = [item for item in bars if item is not None]
        flats = sum(1 for item in observations if str(item[f"outcome_{target}"]) == "flat")
        target_stats[target] = {
            "avg_bars_to_resolution": _json_safe(_average(bars)),
            "median_bars_to_resolution": _json_safe(_median(bars)),
            "flats": flats,
        }
    return {
        "observations_by_signal_hour_utc": {
            str(hour): hours[hour]
            for hour in sorted(hours)
        },
        "target_resolution": target_stats,
        "timeout_heavy_groups": _timeout_heavy_groups(observations),
    }


def _warning_flags(observations: Sequence[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    total = len(observations)
    if total < 30:
        warnings.append("overall sample size below 30")
    if total == 0:
        return warnings

    symbol_counts = Counter(str(item["symbol"]) for item in observations)
    direction_counts = Counter(str(item["signal_direction"]) for item in observations)
    if symbol_counts and max(symbol_counts.values()) / total > 0.5:
        warnings.append("symbol concentration above 50 percent")
    if direction_counts:
        long_count = direction_counts.get("long", 0)
        short_count = direction_counts.get("short", 0)
        if total and abs(long_count - short_count) / total > 0.25:
            warnings.append("long/short imbalance above 25 percent")

    groups = _group_by(observations, ("symbol", "signal_direction"))
    for group_name, group_items in sorted(groups.items()):
        if len(group_items) < 30:
            warnings.append(f"{group_name} sample size below 30")
        if len(group_items) < 10:
            warnings.append(f"{group_name} subgroup below 10 observations; unreliable")
        for target in TARGETS:
            metrics = _target_metrics(group_items, target)
            flat_rate = metrics["flat_rate"]
            if flat_rate is not None and Decimal(str(flat_rate)) >= Decimal("0.50"):
                warnings.append(f"{group_name} {target} high flat rate")

    overall = _metrics_for_groups({"all": observations})["all"]
    if Decimal(str(overall["2r"]["flat_rate"])) >= Decimal("0.50"):
        warnings.append("2R target likely too far: overall flat rate is high")
    return sorted(set(warnings))


def _timeout_heavy_groups(observations: Sequence[dict[str, object]]) -> list[str]:
    output: list[str] = []
    groups = _group_by(observations, ("symbol", "signal_direction"))
    for group_name, group_items in sorted(groups.items()):
        metrics = _target_metrics(group_items, "2r")
        flat_rate = metrics["flat_rate"]
        if flat_rate is not None and Decimal(str(flat_rate)) >= Decimal("0.50"):
            output.append(group_name)
    return output


def _group_by(
    observations: Sequence[dict[str, object]],
    keys: tuple[str, ...],
) -> dict[str, list[dict[str, object]]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in observations:
        group_name = " / ".join(str(item[key]) for key in keys)
        groups[group_name].append(item)
    return dict(groups)


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


def _max_consecutive_losses(observations: Sequence[dict[str, object]], target: str) -> int:
    current = 0
    maximum = 0
    for item in sorted(observations, key=lambda value: str(value.get("signal_time", ""))):
        if str(item[f"outcome_{target}"]) == "loss":
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return maximum


def _mae_buckets(values: Iterable[Decimal | None]) -> dict[str, int]:
    buckets = {
        "<=0.25R": 0,
        "<=0.50R": 0,
        "<=0.75R": 0,
        "<=1.00R": 0,
        ">1.00R": 0,
    }
    for value in values:
        if value is None:
            continue
        adverse = abs(min(value, Decimal("0")))
        if adverse <= Decimal("0.25"):
            buckets["<=0.25R"] += 1
        elif adverse <= Decimal("0.50"):
            buckets["<=0.50R"] += 1
        elif adverse <= Decimal("0.75"):
            buckets["<=0.75R"] += 1
        elif adverse <= Decimal("1.00"):
            buckets["<=1.00R"] += 1
        else:
            buckets[">1.00R"] += 1
    return buckets


def _mfe_buckets(values: Iterable[Decimal | None]) -> dict[str, int]:
    buckets = {
        "<0.50R": 0,
        "0.50R_to_<1.00R": 0,
        "1.00R_to_<1.50R": 0,
        "1.50R_to_<2.00R": 0,
        ">=2.00R": 0,
    }
    for value in values:
        if value is None:
            continue
        if value < Decimal("0.50"):
            buckets["<0.50R"] += 1
        elif value < Decimal("1.00"):
            buckets["0.50R_to_<1.00R"] += 1
        elif value < Decimal("1.50"):
            buckets["1.00R_to_<1.50R"] += 1
        elif value < Decimal("2.00"):
            buckets["1.50R_to_<2.00R"] += 1
        else:
            buckets[">=2.00R"] += 1
    return buckets


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _format_metric_lines(target: str, metrics: dict[str, object]) -> list[str]:
    return [
        f"target: {target}",
        f"  observations: {metrics['observations']}",
        f"  resolved: {metrics['resolved']}",
        f"  wins/losses/flats: {metrics['wins']}/{metrics['losses']}/{metrics['flats']}",
        f"  win_rate: {metrics['win_rate']}",
        f"  loss_rate: {metrics['loss_rate']}",
        f"  flat_rate: {metrics['flat_rate']}",
        f"  expectancy_r: {metrics['expectancy_r']}",
        f"  profit_factor: {metrics['profit_factor']}",
        f"  avg_mae_r: {metrics['avg_mae_r']}",
        f"  avg_mfe_r: {metrics['avg_mfe_r']}",
        f"  avg_bars_to_resolution: {metrics['avg_bars_to_resolution']}",
    ]


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, TargetMetrics):
        return {
            field: _json_safe(getattr(value, field))
            for field in TargetMetrics.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
