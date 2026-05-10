"""Stage 54-SQ C7 expanded validation analyzer.

Research-only. Implements the C7 gate per
``docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md``.

This module produces evidence only. It does not authorize paper trading,
runtime wiring, trading readiness, or live readiness. Detector and frozen
components in ``setup_c_tsmom`` are not modified.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle, normalize_utc, parse_iso_utc
from .setup_c_tsmom import (
    ATR_PERIOD,
    COST_BPS,
    FUNDING_INTERVALS_PER_REBALANCE,
    FUNDING_RATES_PER_8H,
    PRIMARY_COST_SCENARIO,
    PRIMARY_GATE_METRIC,
    PRIMARY_LOOKBACK,
    RANDOM_ITERATIONS,
    RANDOM_SEED,
    REBALANCE_BARS,
    TsmomInterval,
    _funding_impact_normalized,
    _json_safe,
    _median,
    build_tsmom_intervals,
    cost_return,
    count_vol_proxy_skipped_intervals,
    random_baseline_summary,
    summarize_intervals,
    turnover_units,
)


FROZEN_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
DEV_WINDOW_START: datetime = parse_iso_utc("2023-12-17T16:00:00+00:00")
DEV_WINDOW_END: datetime = parse_iso_utc("2026-05-06T08:00:00+00:00")
C7_FUNDING_SCENARIO: str = "high_cost"
COMBINED_RETENTION_THRESHOLD: Decimal = Decimal("0.50")
TWO_OF_THREE_SYMBOLS_REQUIRED: int = 2
RESULT_PASS: str = "C7_PASS"
RESULT_HOLD: str = "C7_HOLD"
RESULT_FAIL: str = "C7_FAIL"
EXPANSION_DIRECTIONS: tuple[str, ...] = ("backward", "forward", "both")
RANDOM_BASELINE_SEED: int = RANDOM_SEED + PRIMARY_LOOKBACK
REPORT_SCHEMA: str = "setup_c_c7_expanded_validation_report_v1"


def analyze_c7_expanded_validation(
    *,
    development_candles_by_symbol: dict[str, Sequence[Candle]],
    expanded_candles_by_symbol: dict[str, Sequence[Candle]],
    expanded_window_start: datetime | str,
    expanded_window_end: datetime | str,
    expansion_direction: str,
    data_source_attribution: dict[str, object] | None = None,
) -> dict[str, object]:
    """Run C7 expanded-validation analysis from candle inputs.

    Research-only. The returned report does not authorize paper, runtime,
    trading, or live readiness. Symbol set and timeframe are frozen; expanded
    candles must be strictly outside the inclusive development window.
    """

    locked_start = _coerce_utc(expanded_window_start)
    locked_end = _coerce_utc(expanded_window_end)
    _validate_locked_window(locked_start, locked_end, expansion_direction)
    _reject_extra_symbol_keys(development_candles_by_symbol)
    _reject_extra_symbol_keys(expanded_candles_by_symbol)
    _reject_dev_window_overlap(
        expanded_candles_by_symbol,
        locked_start=locked_start,
        locked_end=locked_end,
    )

    dev_present = {
        sym: list(candles)
        for sym, candles in development_candles_by_symbol.items()
        if sym in FROZEN_SYMBOLS and len(candles) > 0
    }
    expanded_present = {
        sym: list(candles)
        for sym, candles in expanded_candles_by_symbol.items()
        if sym in FROZEN_SYMBOLS and len(candles) > 0
    }
    dev_intervals = (
        build_tsmom_intervals(dev_present, lookback=PRIMARY_LOOKBACK)
        if dev_present
        else []
    )
    expanded_intervals = (
        build_tsmom_intervals(expanded_present, lookback=PRIMARY_LOOKBACK)
        if expanded_present
        else []
    )
    dev_by_symbol = _group_by_symbol(dev_intervals)
    expanded_by_symbol = _group_by_symbol(expanded_intervals)

    expanded_bars_by_symbol = {
        sym: len(expanded_candles_by_symbol.get(sym, ())) for sym in FROZEN_SYMBOLS
    }
    dev_bars_by_symbol = {
        sym: len(development_candles_by_symbol.get(sym, ())) for sym in FROZEN_SYMBOLS
    }
    if expanded_present:
        vol_proxy_skipped_expanded: dict[str, object] = count_vol_proxy_skipped_intervals(
            expanded_present, lookback=PRIMARY_LOOKBACK
        )
    else:
        vol_proxy_skipped_expanded = {
            "total": 0,
            "by_symbol": {sym: 0 for sym in FROZEN_SYMBOLS},
            "downstream_policy": "no expanded candles supplied",
        }

    return evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=dev_by_symbol,
        expanded_intervals_by_symbol=expanded_by_symbol,
        expanded_window_start=locked_start,
        expanded_window_end=locked_end,
        expansion_direction=expansion_direction,
        expanded_bars_by_symbol=expanded_bars_by_symbol,
        dev_bars_by_symbol=dev_bars_by_symbol,
        vol_proxy_skipped_expanded=vol_proxy_skipped_expanded,
        data_source_attribution=data_source_attribution,
    )


def evaluate_c7_expanded_intervals(
    *,
    dev_intervals_by_symbol: dict[str, Sequence[TsmomInterval]],
    expanded_intervals_by_symbol: dict[str, Sequence[TsmomInterval]],
    expanded_window_start: datetime | str,
    expanded_window_end: datetime | str,
    expansion_direction: str,
    expanded_bars_by_symbol: dict[str, int] | None = None,
    dev_bars_by_symbol: dict[str, int] | None = None,
    vol_proxy_skipped_expanded: dict[str, object] | None = None,
    data_source_attribution: dict[str, object] | None = None,
) -> dict[str, object]:
    """Evaluate the C7 gate from pre-built dev and expanded intervals."""

    locked_start = _coerce_utc(expanded_window_start)
    locked_end = _coerce_utc(expanded_window_end)
    _validate_locked_window(locked_start, locked_end, expansion_direction)
    _reject_extra_symbol_keys(dev_intervals_by_symbol)
    _reject_extra_symbol_keys(expanded_intervals_by_symbol)

    dev_normalized: dict[str, list[TsmomInterval]] = {
        sym: list(dev_intervals_by_symbol.get(sym, ())) for sym in FROZEN_SYMBOLS
    }
    expanded_normalized: dict[str, list[TsmomInterval]] = {
        sym: list(expanded_intervals_by_symbol.get(sym, ())) for sym in FROZEN_SYMBOLS
    }
    expanded_flat: list[TsmomInterval] = sorted(
        (item for sym in FROZEN_SYMBOLS for item in expanded_normalized[sym]),
        key=lambda item: (item.timestamp, item.symbol),
    )

    expanded_bars_by_symbol = expanded_bars_by_symbol or {sym: 0 for sym in FROZEN_SYMBOLS}
    dev_bars_by_symbol = dev_bars_by_symbol or {sym: 0 for sym in FROZEN_SYMBOLS}

    symbols_usable = sorted(sym for sym in FROZEN_SYMBOLS if expanded_normalized[sym])
    symbols_missing = sorted(set(FROZEN_SYMBOLS) - set(symbols_usable))

    per_symbol_counts = {
        sym: {
            "expanded_bars": expanded_bars_by_symbol.get(sym, 0),
            "expanded_intervals": len(expanded_normalized[sym]),
            "dev_bars": dev_bars_by_symbol.get(sym, 0),
            "dev_intervals": len(dev_normalized[sym]),
        }
        for sym in FROZEN_SYMBOLS
    }

    expanded_summary = summarize_intervals(expanded_flat)
    expanded_vt_post_cost = _decimal_or_zero(
        expanded_summary["volatility_targeted_post_cost_return"][PRIMARY_COST_SCENARIO]
    )

    funding_rate = FUNDING_RATES_PER_8H[C7_FUNDING_SCENARIO]
    funding_impact = sum(
        (_funding_impact_normalized(item, funding_rate) for item in expanded_flat),
        Decimal("0"),
    )
    funding_adjusted = expanded_vt_post_cost + funding_impact

    per_symbol_vt: dict[str, Decimal | None] = {}
    symbols_non_negative = 0
    for sym in FROZEN_SYMBOLS:
        intervals = expanded_normalized[sym]
        if not intervals:
            per_symbol_vt[sym] = None
            continue
        symbol_value = _decimal_or_zero(
            summarize_intervals(intervals)[
                "volatility_targeted_post_cost_return"
            ][PRIMARY_COST_SCENARIO]
        )
        per_symbol_vt[sym] = symbol_value
        if symbol_value >= Decimal("0"):
            symbols_non_negative += 1

    if expanded_flat:
        baseline = random_baseline_summary(
            expanded_flat,
            iterations=RANDOM_ITERATIONS,
            seed=RANDOM_BASELINE_SEED,
        )
        random_p75 = _decimal_or_none(baseline["full"]["p75"])
    else:
        random_p75 = None

    union_by_symbol = {
        sym: list(dev_normalized[sym]) + list(expanded_normalized[sym])
        for sym in FROZEN_SYMBOLS
    }
    combined_numerator = combined_window_vt_post_cost_moderate(union_by_symbol)
    combined_denominator = combined_window_vt_post_cost_moderate(dev_normalized)
    if combined_denominator == Decimal("0"):
        combined_ratio: Decimal | None = None
    else:
        combined_ratio = combined_numerator / combined_denominator

    expanded_vol_thresholds = _expanded_vol_thresholds(expanded_flat)
    expanded_regime = _expanded_regime_split(
        expanded_flat, expanded_vol_thresholds["threshold"]
    )

    cond_1_passes = expanded_vt_post_cost > Decimal("0")
    cond_2_passes = (random_p75 is not None) and (expanded_vt_post_cost > random_p75)
    cond_3_passes = funding_adjusted > Decimal("0")
    cond_4_passes = symbols_non_negative >= TWO_OF_THREE_SYMBOLS_REQUIRED
    cond_5_passes = (combined_ratio is not None) and (
        combined_ratio >= COMBINED_RETENTION_THRESHOLD
    )

    all_pass = (
        cond_1_passes
        and cond_2_passes
        and cond_3_passes
        and cond_4_passes
        and cond_5_passes
    )
    all_symbols_usable = len(symbols_missing) == 0

    if not cond_1_passes:
        decision = RESULT_FAIL
    elif not all_symbols_usable:
        decision = RESULT_HOLD
    elif all_pass:
        decision = RESULT_PASS
    else:
        decision = RESULT_HOLD

    if vol_proxy_skipped_expanded is None:
        vol_proxy_skipped_expanded = {
            "total": 0,
            "by_symbol": {sym: 0 for sym in FROZEN_SYMBOLS},
            "downstream_policy": "intervals supplied directly to evaluator",
        }

    if data_source_attribution is None:
        data_source_attribution = {
            "source": "public_bitget_4h_ohlcv",
            "download_metadata": None,
            "single_download_policy": (
                "one approved public download before analysis; no re-download "
                "after seeing results"
            ),
        }

    report = {
        "schema": REPORT_SCHEMA,
        "scope": "research_only_local_4h_ohlcv_expanded_holdout",
        "design_lock": "docs/STAGE_54_SQ_C7_EXPANDED_VALIDATION_DESIGN_LOCK.md",
        "expanded_window_start": locked_start.isoformat(),
        "expanded_window_end": locked_end.isoformat(),
        "expansion_direction": expansion_direction,
        "dev_window_start": DEV_WINDOW_START.isoformat(),
        "dev_window_end": DEV_WINDOW_END.isoformat(),
        "primary_lookback": PRIMARY_LOOKBACK,
        "rebalance_bars": REBALANCE_BARS,
        "atr_period": ATR_PERIOD,
        "primary_cost_scenario": PRIMARY_COST_SCENARIO,
        "primary_gate_metric": PRIMARY_GATE_METRIC,
        "symbols_evaluated": list(FROZEN_SYMBOLS),
        "symbols_usable": symbols_usable,
        "symbols_missing": symbols_missing,
        "per_symbol_counts": per_symbol_counts,
        "expanded_summary": expanded_summary,
        "expanded_vol_thresholds": expanded_vol_thresholds,
        "expanded_regime_split": expanded_regime,
        "vol_proxy_skipped_intervals_expanded": vol_proxy_skipped_expanded,
        "funding_scenario": C7_FUNDING_SCENARIO,
        "funding_rate_per_8h": funding_rate,
        "funding_intervals_per_rebalance": FUNDING_INTERVALS_PER_REBALANCE,
        "funding_impact_on_expanded_vt_post_cost_moderate": funding_impact,
        "funding_adjusted_expanded_vt_post_cost_moderate_high_cost": funding_adjusted,
        "random_seed": RANDOM_BASELINE_SEED,
        "random_iterations": RANDOM_ITERATIONS,
        "random_p75_expanded": random_p75,
        "per_symbol_expanded_vt_post_cost_moderate": per_symbol_vt,
        "symbols_non_negative_count": symbols_non_negative,
        "combined_retention_numerator": combined_numerator,
        "combined_retention_denominator": combined_denominator,
        "combined_retention_ratio": combined_ratio,
        "combined_retention_threshold": COMBINED_RETENTION_THRESHOLD,
        "combined_retention_passes": cond_5_passes,
        "gate_conditions": {
            "expanded_vt_post_cost_moderate_gt_0": {
                "value": expanded_vt_post_cost,
                "threshold": Decimal("0"),
                "passes": cond_1_passes,
            },
            "expanded_beats_random_p75": {
                "value": expanded_vt_post_cost,
                "threshold": random_p75,
                "passes": cond_2_passes,
            },
            "funding_adjusted_high_cost_gt_0": {
                "value": funding_adjusted,
                "threshold": Decimal("0"),
                "passes": cond_3_passes,
            },
            "two_of_three_symbols_non_negative": {
                "value": symbols_non_negative,
                "threshold": TWO_OF_THREE_SYMBOLS_REQUIRED,
                "passes": cond_4_passes,
            },
            "combined_retention_ratio_gte_50pct": {
                "value": combined_ratio,
                "threshold": COMBINED_RETENTION_THRESHOLD,
                "passes": cond_5_passes,
            },
        },
        "decision": decision,
        "data_source_attribution": data_source_attribution,
        "no_readiness_disclaimer": (
            "C7 is research-only. No paper, runtime, trading, or live readiness "
            "is claimed by this report. See design lock section "
            "'What C7 Does Not Authorize'."
        ),
        "known_limitations": [
            "expanded window evidence is a single-block holdout",
            "no parameter optimization is allowed in C7",
            "regime diagnostics are observational only",
            "funding stress is in-gate only at high_cost = 0.0003 per 8H",
        ],
    }
    return _json_safe(report)  # type: ignore[return-value]


def format_c7_report(report: dict[str, object]) -> str:
    """Format a deterministic Setup C C7 expanded validation text report."""

    lines: list[str] = [
        "Setup C C7 expanded validation report",
        "",
        "Scope: research-only expanded-holdout 4H OHLCV evaluation.",
        "No paper/runtime/trading/live readiness claim.",
        "",
        f"decision: {report['decision']}",
        f"schema: {report['schema']}",
        f"expansion_direction: {report['expansion_direction']}",
        f"expanded_window_start: {report['expanded_window_start']}",
        f"expanded_window_end: {report['expanded_window_end']}",
        f"dev_window_start: {report['dev_window_start']}",
        f"dev_window_end: {report['dev_window_end']}",
        f"primary_lookback: {report['primary_lookback']}",
        "",
        "Gate conditions",
    ]
    gate_conditions: dict[str, object] = report["gate_conditions"]  # type: ignore[assignment]
    for name, cond in gate_conditions.items():
        lines.append(
            f"  {name}: value={cond['value']}, "  # type: ignore[index]
            f"threshold={cond['threshold']}, "  # type: ignore[index]
            f"passes={cond['passes']}"  # type: ignore[index]
        )
    lines.extend(
        [
            "",
            "Combined retention",
            f"  numerator: {report['combined_retention_numerator']}",
            f"  denominator: {report['combined_retention_denominator']}",
            f"  ratio: {report['combined_retention_ratio']}",
            f"  threshold: {report['combined_retention_threshold']}",
            f"  passes: {report['combined_retention_passes']}",
            "",
            "Funding (high_cost)",
            f"  scenario: {report['funding_scenario']}",
            f"  rate_per_8h: {report['funding_rate_per_8h']}",
            f"  intervals_per_rebalance: {report['funding_intervals_per_rebalance']}",
            "  funding_impact_on_expanded_vt_post_cost_moderate: "
            f"{report['funding_impact_on_expanded_vt_post_cost_moderate']}",
            "  funding_adjusted_expanded_vt_post_cost_moderate_high_cost: "
            f"{report['funding_adjusted_expanded_vt_post_cost_moderate_high_cost']}",
            "",
            "Random baseline",
            f"  seed: {report['random_seed']}",
            f"  iterations: {report['random_iterations']}",
            f"  p75_expanded: {report['random_p75_expanded']}",
            "",
            "Symbols",
            f"  evaluated: {report['symbols_evaluated']}",
            f"  usable: {report['symbols_usable']}",
            f"  missing: {report['symbols_missing']}",
            f"  non_negative_count: {report['symbols_non_negative_count']}",
            "",
            "Per-symbol expanded vt-post-cost-moderate",
        ]
    )
    per_symbol_vt: dict[str, object] = report["per_symbol_expanded_vt_post_cost_moderate"]  # type: ignore[assignment]
    for sym, value in per_symbol_vt.items():
        lines.append(f"  {sym}: {value}")
    lines.extend(
        [
            "",
            "No-readiness disclaimer",
            f"  {report['no_readiness_disclaimer']}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_c7_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic text and JSON C7 evidence artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_c7_report(report), encoding="utf-8")
    json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def combined_window_vt_post_cost_moderate(
    intervals_by_symbol: dict[str, Sequence[TsmomInterval]],
) -> Decimal:
    """Per-symbol chronological recomputation of vt-post-cost-moderate.

    Resets ``prior_direction = 0`` per symbol and walks intervals in
    timestamp order. Recomputes only the boundary turnover and cost; does
    not recompute interval direction or vol_proxy. Used for both the
    development-only denominator and the dev+expanded numerator so the two
    are computed by an identical routine.
    """

    total = Decimal("0")
    for symbol in sorted(intervals_by_symbol):
        ordered = sorted(
            intervals_by_symbol[symbol], key=lambda item: item.timestamp
        )
        prior_direction = 0
        for interval in ordered:
            turnover = turnover_units(prior_direction, interval.direction)
            prior_direction = interval.direction
            cost = cost_return(turnover, COST_BPS[PRIMARY_COST_SCENARIO])
            post_cost = interval.gross_return - cost
            total += post_cost / interval.vol_proxy
    return total


def _coerce_utc(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return normalize_utc(value)
    return parse_iso_utc(value)


def _validate_locked_window(
    start: datetime, end: datetime, direction: str
) -> None:
    if direction not in EXPANSION_DIRECTIONS:
        raise ValueError(
            f"invalid expansion_direction: {direction!r}; "
            f"must be one of {list(EXPANSION_DIRECTIONS)}"
        )
    if start >= end:
        raise ValueError(
            "expanded_window_start must be strictly before expanded_window_end"
        )
    if direction == "backward":
        if start >= DEV_WINDOW_START:
            raise ValueError(
                "backward expansion start must be strictly before dev_window_start"
            )
        if end >= DEV_WINDOW_START:
            raise ValueError(
                "backward expansion end must be strictly before dev_window_start"
            )
    elif direction == "forward":
        if start <= DEV_WINDOW_END:
            raise ValueError(
                "forward expansion start must be strictly after dev_window_end"
            )
        if end <= DEV_WINDOW_END:
            raise ValueError(
                "forward expansion end must be strictly after dev_window_end"
            )
    elif direction == "both":
        if not (start < DEV_WINDOW_START and end > DEV_WINDOW_END):
            raise ValueError(
                "both expansion must straddle dev window strictly on each side"
            )


def _reject_extra_symbol_keys(by_symbol: dict[str, object]) -> None:
    extras = sorted(set(by_symbol.keys()) - set(FROZEN_SYMBOLS))
    if extras:
        raise ValueError(
            "unexpected symbol keys (frozen set is "
            f"{list(FROZEN_SYMBOLS)}): {extras}"
        )


def _reject_dev_window_overlap(
    expanded_candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    locked_start: datetime,
    locked_end: datetime,
) -> None:
    for symbol, candles in expanded_candles_by_symbol.items():
        for candle in candles:
            ts = candle.timestamp
            if DEV_WINDOW_START <= ts <= DEV_WINDOW_END:
                raise ValueError(
                    f"{symbol}: candle at {ts.isoformat()} overlaps inclusive "
                    f"dev window [{DEV_WINDOW_START.isoformat()}, "
                    f"{DEV_WINDOW_END.isoformat()}]"
                )
            if ts < locked_start or ts > locked_end:
                raise ValueError(
                    f"{symbol}: candle at {ts.isoformat()} is outside locked "
                    f"expanded window [{locked_start.isoformat()}, "
                    f"{locked_end.isoformat()}]"
                )


def _group_by_symbol(
    intervals: Sequence[TsmomInterval],
) -> dict[str, list[TsmomInterval]]:
    groups: dict[str, list[TsmomInterval]] = defaultdict(list)
    for item in intervals:
        groups[item.symbol].append(item)
    return dict(groups)


def _expanded_vol_thresholds(
    intervals: Sequence[TsmomInterval],
) -> dict[str, object]:
    threshold = (
        _median([item.vol_proxy for item in intervals]) if intervals else None
    )
    return {
        "threshold": threshold,
        "derived_from": "expanded_window_only",
        "rule": (
            "high_vol if interval ATR/close proxy is greater than or equal "
            "to expanded-window median"
        ),
        "policy": "no development-window threshold leakage",
    }


def _expanded_regime_split(
    intervals: Sequence[TsmomInterval],
    threshold: Decimal | None,
) -> dict[str, object]:
    if not intervals or threshold is None:
        return {
            "high_vol": summarize_intervals([]),
            "low_vol": summarize_intervals([]),
            "policy": {
                "diagnostic_only": True,
                "candidate_inclusion_unchanged": True,
                "strategy_filter_introduced": False,
                "primary_gate_unchanged": True,
                "high_low_threshold_source": "expanded_window_only",
            },
        }
    high_vol = [item for item in intervals if item.vol_proxy >= threshold]
    low_vol = [item for item in intervals if item.vol_proxy < threshold]
    return {
        "high_vol": summarize_intervals(high_vol),
        "low_vol": summarize_intervals(low_vol),
        "policy": {
            "diagnostic_only": True,
            "candidate_inclusion_unchanged": True,
            "strategy_filter_introduced": False,
            "primary_gate_unchanged": True,
            "high_low_threshold_source": "expanded_window_only",
        },
    }


def _decimal_or_zero(value: object) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
