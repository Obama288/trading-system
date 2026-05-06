"""Conditional diagnostics for Setup B signal observations.

Produces per-bucket metrics conditioned on six tag types:
session, volatility_regime, slow_trend_state, htf_alignment, mfe_shape, flat_decomp.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle, parse_iso_utc
from .indicators import atr as compute_atr


TARGETS = ("1r", "1_5r", "2r")
TARGET_R_VALUES = {"1r": Decimal("1"), "1_5r": Decimal("1.5"), "2r": Decimal("2")}
SAMPLE_SIZE_FLAG_THRESHOLD = 10
SMA_PERIOD = 50
ATR_PERIOD = 14

MFE_GE_1_0R = Decimal("1")
MFE_GE_0_5R = Decimal("0.5")
MFE_GE_0_3R = Decimal("0.3")

FLAT_NEAR_WIN_MFE = Decimal("0.8")
FLAT_ADVERSE_MAE = Decimal("-0.6")
FLAT_DEAD_FLAT_MFE = Decimal("0.3")
FLAT_DEAD_FLAT_MAE = Decimal("-0.3")

TAG_KEYS = (
    "session",
    "volatility_regime",
    "slow_trend_state",
    "htf_alignment",
    "mfe_shape",
    "flat_decomp",
)


def tag_observations(
    observations: Sequence[dict[str, object]],
    candles_by_symbol: dict[str, Sequence[Candle]],
) -> list[dict[str, object]]:
    """Attach six conditional tags to each observation."""

    atr_series_by_symbol = _build_atr_series(candles_by_symbol)
    atr_thresholds = _build_atr_thresholds(atr_series_by_symbol)
    sma_series_by_symbol = _build_sma_series(candles_by_symbol)
    ts_index_by_symbol = _build_timestamp_index_map(candles_by_symbol)

    tagged: list[dict[str, object]] = []
    for obs in observations:
        symbol = str(obs["symbol"])
        signal_time_str = str(obs["signal_time"])
        entry_price = Decimal(str(obs["entry_price"]))
        atr_at_entry = Decimal(str(obs["atr_at_entry"]))

        candle_index = ts_index_by_symbol.get(symbol, {}).get(signal_time_str)

        result = dict(obs)
        result["tag_session"] = str(obs.get("session_label", "unknown"))
        result["tag_volatility_regime"] = _volatility_regime_tag(atr_at_entry, symbol, atr_thresholds)
        result["tag_slow_trend_state"] = _slow_trend_state_tag(
            entry_price, symbol, candle_index, sma_series_by_symbol
        )
        result["tag_htf_alignment"] = "not_available"
        raw_mfe_1r = obs.get("mfe_1r")
        raw_mae_1r = obs.get("mae_1r")
        mfe_1r = Decimal(str(raw_mfe_1r)) if raw_mfe_1r is not None else None
        mae_1r = Decimal(str(raw_mae_1r)) if raw_mae_1r is not None else None
        result["tag_mfe_shape"] = _mfe_shape_tag(mfe_1r)
        result["tag_flat_decomp"] = _flat_decomp_tag(
            outcome=str(obs["outcome_1r"]),
            mfe_r=mfe_1r,
            mae_r=mae_1r,
        )
        tagged.append(result)

    return tagged


def compute_conditional_metrics(
    tagged_observations: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Compute per-bucket metrics for each tag type."""

    output: dict[str, object] = {}
    for tag_key in TAG_KEYS:
        field = f"tag_{tag_key}"
        buckets: dict[str, list[dict[str, object]]] = {}
        for obs in tagged_observations:
            val = str(obs.get(field, "unknown"))
            if val not in buckets:
                buckets[val] = []
            buckets[val].append(obs)  # type: ignore[arg-type]
        output[tag_key] = {
            val: {target: _bucket_metrics(group, target) for target in TARGETS}
            for val, group in sorted(buckets.items())
        }
    return output


def build_conditional_report(
    observations: Sequence[dict[str, object]],
    candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    random_1r_median_expectancy: Decimal | None = None,
) -> dict[str, object]:
    """Build the full conditional diagnostics report."""

    tagged = tag_observations(observations, candles_by_symbol)
    conditional_metrics = compute_conditional_metrics(tagged)
    tag_dist = _tag_distributions(tagged)

    overall_1r = _bucket_metrics(tagged, "1r")
    raw_exp = overall_1r.get("expectancy_r")
    overall_1r_expectancy = Decimal(str(raw_exp)) if raw_exp is not None else Decimal("0")

    gate = _decision_gate(
        conditional_metrics,
        overall_1r_expectancy=overall_1r_expectancy,
        random_1r_median_expectancy=random_1r_median_expectancy,
    )

    return _json_safe(
        {
            "schema": "setup_b_conditional_diagnostics_v1",
            "observation_count": len(observations),
            "tag_distributions": tag_dist,
            "conditional_metrics": conditional_metrics,
            "decision_gate": gate,
        }
    )


def write_conditional_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic conditional diagnostics artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_conditional_report(report), encoding="utf-8")
    json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def format_conditional_report(report: dict[str, object]) -> str:
    """Format a stable text report for the conditional diagnostics."""

    lines = [
        "Setup B conditional diagnostics",
        "",
        "Scope: exploratory conditional diagnostics only.",
        "No profitability, paper-trading, live-trading, or readiness claim.",
        "",
        f"observations: {report['observation_count']}",
    ]

    cond = report["conditional_metrics"]  # type: ignore[index]
    dist = report["tag_distributions"]  # type: ignore[index]

    for tag_key in TAG_KEYS:
        if tag_key not in cond:
            continue
        lines.extend(["", f"Tag: {tag_key}"])
        for bucket_val in sorted(cond[tag_key]):  # type: ignore[union-attr]
            bucket_n = int(dist.get(tag_key, {}).get(bucket_val, 0))  # type: ignore[union-attr]
            flag_note = " [small_sample]" if bucket_n < SAMPLE_SIZE_FLAG_THRESHOLD else ""
            lines.append(f"  {bucket_val} (n={bucket_n}{flag_note})")
            for target in TARGETS:
                m = cond[tag_key][bucket_val].get(target, {})  # type: ignore[union-attr]
                if not m:
                    continue
                lines.append(
                    f"    {target}: W/L/F={m['wins']}/{m['losses']}/{m['flats']}"
                    f" win_rate={m['win_rate']} expectancy_r={m['expectancy_r']}"
                    f" avg_mfe={m['avg_mfe_r']} avg_mae={m['avg_mae_r']}"
                    f" p_1r|0.5r={m['p_reach_1r_given_reach_0_5r']}"
                )

    gate = report["decision_gate"]  # type: ignore[index]
    lines.extend(
        [
            "",
            "Decision gate (primary target: 1r)",
            f"  overall_1r_expectancy_r: {gate['overall_1r_expectancy_r']}",
            f"  random_1r_median_expectancy_r: {gate['random_1r_median_expectancy_r']}",
            "",
            "  Flagged conditions (expectancy_r_1r > overall or > random median):",
        ]
    )
    flags = gate["flags"]  # type: ignore[index]
    if flags:
        for flag in sorted(flags, key=lambda f: str(f["tag"])):  # type: ignore[arg-type]
            badges: list[str] = []
            if flag["beats_overall"]:
                badges.append("beats_overall")
            if flag["beats_random_median"]:
                badges.append("beats_random")
            small = " [small_sample]" if flag["sample_size_flag"] else ""
            lines.append(
                f"    {flag['tag']}: expectancy_r={flag['expectancy_r_1r']}"
                f" n={flag['n']} {', '.join(badges)}{small}"
            )
    else:
        lines.append("    (none)")

    lines.extend(["", f"  Summary: {gate['summary']}"])
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Tag computation helpers
# ---------------------------------------------------------------------------


def _volatility_regime_tag(
    atr_at_entry: Decimal,
    symbol: str,
    thresholds: dict[str, tuple[Decimal, Decimal]],
) -> str:
    if symbol not in thresholds:
        return "atr_unavailable"
    p33, p67 = thresholds[symbol]
    if atr_at_entry < p33:
        return "low"
    if atr_at_entry < p67:
        return "mid"
    return "high"


def _slow_trend_state_tag(
    entry_price: Decimal,
    symbol: str,
    candle_index: int | None,
    sma_series: dict[str, list[Decimal | None]],
) -> str:
    if candle_index is None:
        return "sma_unavailable"
    series = sma_series.get(symbol)
    if series is None or candle_index >= len(series):
        return "sma_unavailable"
    sma_now = series[candle_index]
    if sma_now is None:
        return "sma_unavailable"
    prev_sma = series[candle_index - 1] if candle_index > 0 else None
    position = "above" if entry_price >= sma_now else "below"
    if prev_sma is None:
        slope = "flat"
    elif sma_now > prev_sma:
        slope = "rising"
    elif sma_now < prev_sma:
        slope = "falling"
    else:
        slope = "flat"
    return f"{position}_sma_{slope}"


def _mfe_shape_tag(mfe_1r: Decimal | None) -> str:
    if mfe_1r is None:
        return "mfe_unavailable"
    if mfe_1r >= MFE_GE_1_0R:
        return "mfe_ge_1_0r"
    if mfe_1r >= MFE_GE_0_5R:
        return "mfe_0_5_to_1_0r"
    if mfe_1r >= MFE_GE_0_3R:
        return "mfe_0_3_to_0_5r"
    return "mfe_lt_0_3r"


def _flat_decomp_tag(outcome: str, mfe_r: Decimal | None, mae_r: Decimal | None) -> str:
    if outcome != "flat":
        return outcome
    if mfe_r is None or mae_r is None:
        return "flat_no_excursion_data"
    if mfe_r >= FLAT_NEAR_WIN_MFE:
        return "near_win_flat"
    if mae_r <= FLAT_ADVERSE_MAE:
        return "adverse_flat"
    if mfe_r < FLAT_DEAD_FLAT_MFE and mae_r > FLAT_DEAD_FLAT_MAE:
        return "dead_flat"
    return "ordinary_flat"


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------


def _bucket_metrics(
    observations: Sequence[dict[str, object]], target: str
) -> dict[str, object]:
    target_r = TARGET_R_VALUES[target]
    outcomes = [str(obs[f"outcome_{target}"]) for obs in observations]
    wins = outcomes.count("win")
    losses = outcomes.count("loss")
    flats = outcomes.count("flat")
    n = len(observations)

    r_values = [_outcome_r(outcome, target_r) for outcome in outcomes]
    mae_values = [
        Decimal(str(obs[f"mae_{target}"]))
        for obs in observations
        if obs.get(f"mae_{target}") is not None
    ]
    mfe_values = [
        Decimal(str(obs[f"mfe_{target}"]))
        for obs in observations
        if obs.get(f"mfe_{target}") is not None
    ]

    mfe_1r_values = [
        Decimal(str(obs["mfe_1r"]))
        for obs in observations
        if obs.get("mfe_1r") is not None
    ]
    count_0_5r = sum(1 for v in mfe_1r_values if v >= MFE_GE_0_5R)
    count_1_0r_given_0_5r = sum(
        1 for v in mfe_1r_values if v >= MFE_GE_0_5R and v >= MFE_GE_1_0R
    )
    p_reach = (
        Decimal(count_1_0r_given_0_5r) / Decimal(count_0_5r)
        if count_0_5r > 0
        else None
    )

    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": _rate(wins, n),
        "flat_rate": _rate(flats, n),
        "expectancy_r": _average(r_values),
        "avg_mae_r": _average(mae_values),
        "avg_mfe_r": _average(mfe_values),
        "median_mae_r": _median(mae_values),
        "median_mfe_r": _median(mfe_values),
        "p_reach_1r_given_reach_0_5r": p_reach,
        "sample_size_flag": n < SAMPLE_SIZE_FLAG_THRESHOLD,
    }


def _tag_distributions(
    tagged_observations: Sequence[dict[str, object]],
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for tag_key in TAG_KEYS:
        field = f"tag_{tag_key}"
        counts: dict[str, int] = {}
        for obs in tagged_observations:
            val = str(obs.get(field, "unknown"))
            counts[val] = counts.get(val, 0) + 1
        result[tag_key] = counts
    return result


def _decision_gate(
    conditional_metrics: dict[str, object],
    overall_1r_expectancy: Decimal,
    random_1r_median_expectancy: Decimal | None,
) -> dict[str, object]:
    flags: list[dict[str, object]] = []

    for tag_key, buckets in conditional_metrics.items():
        for bucket_val, target_metrics in buckets.items():  # type: ignore[union-attr]
            m1r = target_metrics.get("1r", {})  # type: ignore[union-attr]
            n = int(m1r.get("n", 0))  # type: ignore[arg-type]
            raw_exp = m1r.get("expectancy_r")  # type: ignore[union-attr]
            if raw_exp is None:
                continue
            exp = Decimal(str(raw_exp))
            beats_overall = exp > overall_1r_expectancy
            beats_random = (
                random_1r_median_expectancy is not None
                and exp > random_1r_median_expectancy
            )
            if beats_overall or beats_random:
                flags.append(
                    {
                        "tag": f"{tag_key}={bucket_val}",
                        "n": n,
                        "sample_size_flag": n < SAMPLE_SIZE_FLAG_THRESHOLD,
                        "expectancy_r_1r": str(exp),
                        "beats_overall": beats_overall,
                        "beats_random_median": beats_random,
                    }
                )

    qualified = sum(1 for f in flags if not f["sample_size_flag"])
    return {
        "overall_1r_expectancy_r": str(overall_1r_expectancy),
        "random_1r_median_expectancy_r": (
            str(random_1r_median_expectancy) if random_1r_median_expectancy is not None else None
        ),
        "flags": flags,
        "summary": (
            f"{qualified} condition(s) beat overall 1r expectancy with n>={SAMPLE_SIZE_FLAG_THRESHOLD}"
        ),
    }


# ---------------------------------------------------------------------------
# Series builders
# ---------------------------------------------------------------------------


def _build_atr_series(
    candles_by_symbol: dict[str, Sequence[Candle]],
) -> dict[str, list[Decimal | None]]:
    return {symbol: compute_atr(candles, ATR_PERIOD) for symbol, candles in candles_by_symbol.items()}


def _build_atr_thresholds(
    atr_series_by_symbol: dict[str, list[Decimal | None]],
) -> dict[str, tuple[Decimal, Decimal]]:
    thresholds: dict[str, tuple[Decimal, Decimal]] = {}
    for symbol, series in atr_series_by_symbol.items():
        valid = sorted(v for v in series if v is not None)
        if len(valid) < 3:
            continue
        p33 = _percentile_value(valid, Decimal("0.333"))
        p67 = _percentile_value(valid, Decimal("0.667"))
        thresholds[symbol] = (p33, p67)
    return thresholds


def _build_sma_series(
    candles_by_symbol: dict[str, Sequence[Candle]],
    period: int = SMA_PERIOD,
) -> dict[str, list[Decimal | None]]:
    result: dict[str, list[Decimal | None]] = {}
    for symbol, candles in candles_by_symbol.items():
        series: list[Decimal | None] = [None] * len(candles)
        for i in range(period - 1, len(candles)):
            window_sum = sum(
                (candles[j].close for j in range(i - period + 1, i + 1)),
                Decimal("0"),
            )
            series[i] = window_sum / Decimal(period)
        result[symbol] = series
    return result


def _build_timestamp_index_map(
    candles_by_symbol: dict[str, Sequence[Candle]],
) -> dict[str, dict[str, int]]:
    return {
        symbol: {candle.timestamp.isoformat(): index for index, candle in enumerate(candles)}
        for symbol, candles in candles_by_symbol.items()
    }


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


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
    return sum(values, Decimal("0")) / Decimal(len(values))


def _median(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    sorted_vals = sorted(values)
    mid = len(sorted_vals) // 2
    if len(sorted_vals) % 2:
        return sorted_vals[mid]
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal("2")


def _percentile_value(sorted_values: list[Decimal], percentile: Decimal) -> Decimal:
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = percentile * Decimal(len(sorted_values) - 1)
    lower = int(rank.to_integral_value(rounding="ROUND_FLOOR"))
    upper = int(rank.to_integral_value(rounding="ROUND_CEILING"))
    if lower == upper:
        return sorted_values[lower]
    fraction = rank - Decimal(lower)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


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
