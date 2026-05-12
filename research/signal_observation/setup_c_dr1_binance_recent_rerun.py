"""Bounded DR1 rerun over committed Binance recent 4H data.

This rerun uses only the committed Binance recent 4H CSV artifacts that passed
the locked recent-data acquisition validation. It does not download data, change
thresholds, expand DR1 scope, or promote readiness.
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle, parse_iso_utc
from .csv_loader import load_ohlcv_csv
from .setup_c_dr1_data_recency_predictability import (
    ANALYSIS_INCONCLUSIVE,
    ANALYSIS_SUPPORTIVE,
    ANALYSIS_WEAK,
    AUTOCORR_SUPPORTIVE_THRESHOLD,
    AUTOCORR_WEAK_THRESHOLD,
    FRESHNESS_MAX_AGE_DAYS,
    FRESHNESS_MIN_MONTHS,
    LEAD_LAG_SUPPORTIVE_THRESHOLD,
    MIN_NON_OVERLAPPING_OBSERVATIONS,
    OUTCOME_HIGH,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_LOW,
    VARIANCE_RATIO_SUPPORTIVE_THRESHOLD,
    VARIANCE_RATIO_WEAK_THRESHOLD,
    _adjacent_same_sign_counts,
    _classify_autocorr,
    _classify_variance_ratio,
    _decimal_string,
    _max_gap,
    _non_overlapping_values,
    _ratio,
    _sample_variance,
    _sign,
    _step_returns,
    _subtract_months,
    classify_dr1_outcome,
    classify_lead_lag,
    non_overlapping_block_returns,
)
from .setup_c_tsmom import (
    PRIMARY_COST_SCENARIO,
    PRIMARY_LOOKBACK,
    REBALANCE_BARS,
    _json_safe,
    build_tsmom_intervals,
    summarize_intervals,
)


REPORT_SCHEMA = "setup_c_dr1_binance_recent_rerun_report_v1"
DESIGN_LOCK = "docs/STAGE_54_SQ_DR1_BINANCE_RECENT_RERUN_DESIGN_LOCK.md"
SOURCE_VALIDATION_REPORT = (
    "research/signal_observation/output/binance_recent/"
    "setup_c_dr1_binance_recent_4h_acquisition_report.json"
)
RERUN_IMPLEMENTATION_DATE = parse_iso_utc("2026-05-12T18:11:06.484354+00:00")
RERUN_WINDOW_START = parse_iso_utc("2025-11-12T12:00:00+00:00")
RERUN_WINDOW_END = parse_iso_utc("2026-05-12T12:00:00+00:00")
VENUE = "binance"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAME = "4H"
EXPECTED_STEP = timedelta(hours=4)
DEFAULT_DATA_DIR = Path("research/signal_observation/data/binance_recent")
DEFAULT_OUTPUT_DIR = Path("research/signal_observation/output/recon")
REPORT_JSON_NAME = "setup_c_dr1_binance_recent_rerun_report.json"
REPORT_TXT_NAME = "setup_c_dr1_binance_recent_rerun_report.txt"


def analyze_dr1_binance_recent_rerun(
    candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    implementation_date=RERUN_IMPLEMENTATION_DATE,
) -> dict[str, object]:
    """Run the locked DR1 Binance recent rerun from committed candles."""

    _validate_symbol_scope(candles_by_symbol)
    freshness = evaluate_binance_recent_freshness(
        candles_by_symbol,
        implementation_date=implementation_date,
    )
    analyses = {
        "non_overlapping_return_autocorrelation": analyze_non_overlapping_autocorrelation(
            candles_by_symbol
        ),
        "variance_ratio_predictability": analyze_variance_ratio(candles_by_symbol),
        "btc_to_eth_sol_lead_lag": analyze_btc_lead_lag(candles_by_symbol),
        "setup_c_recent_out_of_window_persistence": analyze_setup_c_recent_persistence(
            candles_by_symbol
        ),
    }
    decision = classify_dr1_outcome(
        freshness_eligible=bool(freshness["eligible"]),
        analyses=analyses,
    )
    report = {
        "schema": REPORT_SCHEMA,
        "design_lock": DESIGN_LOCK,
        "source_validation_report": SOURCE_VALIDATION_REPORT,
        "scope": "research_only_binance_recent_dr1_rerun",
        "venue": VENUE,
        "symbols": list(SYMBOLS),
        "timeframe": TIMEFRAME,
        "rerun_input_window": rerun_input_window(),
        "implementation_date": implementation_date.isoformat(),
        "primary_lookback": PRIMARY_LOOKBACK,
        "rebalance_bars": REBALANCE_BARS,
        "freshness_eligibility": freshness,
        "analyses": analyses,
        "dr1_rerun_decision": decision,
        "decision_implication": decision_implication(decision),
        "flags": safety_flags(),
    }
    return _json_safe(report)  # type: ignore[return-value]


def evaluate_binance_recent_freshness(
    candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    implementation_date=RERUN_IMPLEMENTATION_DATE,
) -> dict[str, object]:
    """Evaluate the locked freshness requirement for Binance recent data."""

    min_latest = implementation_date - timedelta(days=FRESHNESS_MAX_AGE_DAYS)
    per_symbol: dict[str, dict[str, object]] = {}
    eligible = True
    for symbol in SYMBOLS:
        summary = _freshness_for_symbol(
            candles_by_symbol[symbol],
            symbol=symbol,
            min_latest=min_latest,
        )
        eligible = eligible and bool(summary["sufficient"])
        per_symbol[symbol] = summary
    return {
        "eligible": eligible,
        "implementation_date": implementation_date.isoformat(),
        "minimum_latest_candle": min_latest.isoformat(),
        "minimum_contiguous_months": FRESHNESS_MIN_MONTHS,
        "locked_window_start": RERUN_WINDOW_START.isoformat(),
        "locked_window_end": RERUN_WINDOW_END.isoformat(),
        "per_symbol": per_symbol,
    }


def analyze_non_overlapping_autocorrelation(
    candles_by_symbol: dict[str, Sequence[Candle]],
) -> dict[str, object]:
    """Evaluate same-sign persistence across adjacent non-overlapping returns."""

    pooled_matches = 0
    pooled_observations = 0
    per_symbol: dict[str, dict[str, object]] = {}
    for symbol in SYMBOLS:
        blocks = non_overlapping_block_returns(candles_by_symbol[symbol], symbol=symbol)
        signs = [_sign(block.value) for block in blocks if _sign(block.value) != 0]
        matches, observations = _adjacent_same_sign_counts(signs)
        rate = _ratio(matches, observations)
        pooled_matches += matches
        pooled_observations += observations
        per_symbol[symbol] = {
            "observations": observations,
            "same_sign_count": matches,
            "same_sign_rate": _decimal_string(rate),
            "outcome": _classify_autocorr(rate, observations),
        }
    pooled_rate = _ratio(pooled_matches, pooled_observations)
    return {
        "method": "adjacent same-sign rate over non-overlapping 40-bar returns",
        "pooled_observations": pooled_observations,
        "pooled_same_sign_count": pooled_matches,
        "pooled_same_sign_rate": _decimal_string(pooled_rate),
        "outcome": _classify_autocorr(pooled_rate, pooled_observations),
        "per_symbol": per_symbol,
        "thresholds": {
            "supportive_gt": str(AUTOCORR_SUPPORTIVE_THRESHOLD),
            "weak_lt": str(AUTOCORR_WEAK_THRESHOLD),
            "minimum_observations": MIN_NON_OVERLAPPING_OBSERVATIONS,
        },
    }


def analyze_variance_ratio(
    candles_by_symbol: dict[str, Sequence[Candle]],
) -> dict[str, object]:
    """Evaluate the locked variance-ratio style predictability check."""

    short_returns: list[Decimal] = []
    long_returns: list[Decimal] = []
    for symbol in SYMBOLS:
        candles = list(candles_by_symbol[symbol])
        short_returns.extend(_step_returns(candles, step=1))
        long_returns.extend(_non_overlapping_values(candles, step=PRIMARY_LOOKBACK))
    short_var = _sample_variance(short_returns)
    long_var = _sample_variance(long_returns)
    ratio = None
    if short_var is not None and short_var > Decimal("0") and long_var is not None:
        ratio = long_var / (short_var * Decimal(PRIMARY_LOOKBACK))
    observations = min(len(short_returns), len(long_returns))
    return {
        "method": (
            "variance of non-overlapping 40-bar returns divided by 40 times "
            "one-bar return variance"
        ),
        "short_return_observations": len(short_returns),
        "long_return_observations": len(long_returns),
        "variance_ratio": _decimal_string(ratio),
        "outcome": _classify_variance_ratio(ratio, observations),
        "thresholds": {
            "supportive_gt": str(VARIANCE_RATIO_SUPPORTIVE_THRESHOLD),
            "weak_lt": str(VARIANCE_RATIO_WEAK_THRESHOLD),
            "minimum_long_observations": MIN_NON_OVERLAPPING_OBSERVATIONS,
        },
    }


def analyze_btc_lead_lag(
    candles_by_symbol: dict[str, Sequence[Candle]],
) -> dict[str, object]:
    """Evaluate BTC one-block lead directional agreement for ETH/SOL."""

    matches = 0
    observations = 0
    per_target: dict[str, dict[str, object]] = {}
    btc = non_overlapping_block_returns(candles_by_symbol["BTCUSDT"], symbol="BTCUSDT")
    btc_by_time = {block.timestamp: _sign(block.value) for block in btc}
    for target in ("ETHUSDT", "SOLUSDT"):
        target_matches = 0
        target_observations = 0
        alt = non_overlapping_block_returns(candles_by_symbol[target], symbol=target)
        alt_by_time = {block.timestamp: _sign(block.value) for block in alt}
        ordered_times = sorted(set(btc_by_time).intersection(alt_by_time))
        for index in range(len(ordered_times) - 1):
            btc_sign = btc_by_time[ordered_times[index]]
            alt_sign = alt_by_time[ordered_times[index + 1]]
            if btc_sign == 0 or alt_sign == 0:
                continue
            target_observations += 1
            if btc_sign == alt_sign:
                target_matches += 1
        target_rate = _ratio(target_matches, target_observations)
        per_target[target] = {
            "observations": target_observations,
            "matching_direction_count": target_matches,
            "directional_agreement": _decimal_string(target_rate),
            "outcome": classify_lead_lag(target_rate, target_observations),
        }
        matches += target_matches
        observations += target_observations
    agreement = _ratio(matches, observations)
    return {
        "method": "BTC non-overlapping 40-bar return sign leads ETH/SOL by one block",
        "observations": observations,
        "matching_direction_count": matches,
        "directional_agreement": _decimal_string(agreement),
        "outcome": classify_lead_lag(agreement, observations),
        "per_target": per_target,
        "thresholds": {
            "supportive_gt": str(LEAD_LAG_SUPPORTIVE_THRESHOLD),
            "minimum_observations": MIN_NON_OVERLAPPING_OBSERVATIONS,
        },
        "policy": "below or equal to 60%, or underpowered coverage, is inconclusive",
    }


def analyze_setup_c_recent_persistence(
    candles_by_symbol: dict[str, Sequence[Candle]],
) -> dict[str, object]:
    """Evaluate frozen Setup C persistence on the committed Binance window."""

    intervals = build_tsmom_intervals(candles_by_symbol, lookback=PRIMARY_LOOKBACK)
    summary = summarize_intervals(intervals)
    vt_post_cost = Decimal(
        str(summary["volatility_targeted_post_cost_return"][PRIMARY_COST_SCENARIO])  # type: ignore[index]
    )
    per_symbol = {}
    non_negative_symbols = 0
    for symbol in SYMBOLS:
        symbol_intervals = [item for item in intervals if item.symbol == symbol]
        symbol_summary = summarize_intervals(symbol_intervals)
        symbol_value = Decimal(
            str(
                symbol_summary["volatility_targeted_post_cost_return"][  # type: ignore[index]
                    PRIMARY_COST_SCENARIO
                ]
            )
        )
        if symbol_value >= Decimal("0"):
            non_negative_symbols += 1
        per_symbol[symbol] = {
            "intervals": len(symbol_intervals),
            "vt_post_cost_moderate": str(symbol_value),
        }
    if len(intervals) < MIN_NON_OVERLAPPING_OBSERVATIONS:
        outcome = ANALYSIS_INCONCLUSIVE
    elif vt_post_cost > Decimal("0") and non_negative_symbols >= 2:
        outcome = ANALYSIS_SUPPORTIVE
    else:
        outcome = ANALYSIS_WEAK
    return {
        "method": (
            "frozen Setup C 40-bar volatility-targeted post-cost moderate "
            "on committed Binance recent six-month segment"
        ),
        "intervals": len(intervals),
        "vt_post_cost_moderate": str(vt_post_cost),
        "non_negative_symbols": non_negative_symbols,
        "outcome": outcome,
        "per_symbol": per_symbol,
    }


def load_committed_binance_recent_candles(
    package_dir: Path | None = None,
) -> dict[str, list[Candle]]:
    """Load committed Binance recent CSV artifacts only."""

    root = package_dir or Path(__file__).resolve().parent
    data_dir = root / "data" / "binance_recent"
    return {
        symbol: load_ohlcv_csv(data_dir / f"{symbol}_USDT-FUTURES_4H_recent.csv")
        for symbol in SYMBOLS
    }


def run_dr1_binance_recent_rerun(
    package_dir: Path | None = None,
) -> dict[str, object]:
    """Load committed Binance recent data, run rerun, and write artifacts."""

    root = package_dir or Path(__file__).resolve().parent
    candles = load_committed_binance_recent_candles(root)
    report = analyze_dr1_binance_recent_rerun(candles)
    output_dir = root / "output" / "recon"
    write_rerun_artifacts(
        report,
        text_path=output_dir / REPORT_TXT_NAME,
        json_path=output_dir / REPORT_JSON_NAME,
    )
    return report


def format_rerun_report(report: dict[str, object]) -> str:
    """Format the deterministic DR1 Binance recent rerun report."""

    freshness: dict[str, object] = report["freshness_eligibility"]  # type: ignore[assignment]
    analyses: dict[str, object] = report["analyses"]  # type: ignore[assignment]
    window: dict[str, object] = report["rerun_input_window"]  # type: ignore[assignment]
    lines = [
        "Setup C DR1 Binance recent rerun report",
        "",
        "Scope: research-only committed Binance recent 4H CSV artifacts.",
        "No downloads, no network calls, no threshold changes, no readiness promotion.",
        "",
        f"schema: {report['schema']}",
        f"decision: {report['dr1_rerun_decision']}",
        f"freshness_eligible: {freshness['eligible']}",
        f"window: {window['start_utc']} to {window['end_utc']}",
        "",
        "Analysis outcomes",
    ]
    for name in (
        "non_overlapping_return_autocorrelation",
        "variance_ratio_predictability",
        "btc_to_eth_sol_lead_lag",
        "setup_c_recent_out_of_window_persistence",
    ):
        item: dict[str, object] = analyses[name]  # type: ignore[assignment]
        lines.append(f"  {name}: {item['outcome']}")
        if name == "non_overlapping_return_autocorrelation":
            lines.append(f"    pooled_same_sign_rate: {item['pooled_same_sign_rate']}")
        elif name == "variance_ratio_predictability":
            lines.append(f"    variance_ratio: {item['variance_ratio']}")
        elif name == "btc_to_eth_sol_lead_lag":
            lines.append(f"    directional_agreement: {item['directional_agreement']}")
        elif name == "setup_c_recent_out_of_window_persistence":
            lines.append(f"    vt_post_cost_moderate: {item['vt_post_cost_moderate']}")
    lines.extend(
        [
            "",
            f"decision_implication: {report['decision_implication']}",
            "",
            "Safety flags",
        ]
    )
    flags: dict[str, object] = report["flags"]  # type: ignore[assignment]
    for key in sorted(flags):
        lines.append(f"  {key}: {flags[key]}")
    return "\n".join(lines).rstrip() + "\n"


def write_rerun_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic rerun text and JSON artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_rerun_report(report), encoding="utf-8")
    json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def decision_implication(decision: str) -> str:
    if decision == OUTCOME_HIGH:
        return (
            "A paper-candidate design-lock decision may be considered only if "
            "the owner explicitly chooses to continue."
        )
    if decision == OUTCOME_LOW:
        return (
            "Do not open a paper-candidate design lock; return to owner "
            "decision on parking or structural review."
        )
    if decision == OUTCOME_INCONCLUSIVE:
        return (
            "Define the remaining blocker; do not open a paper-candidate "
            "design lock."
        )
    raise ValueError(f"unknown DR1 rerun decision: {decision!r}")


def safety_flags() -> dict[str, bool]:
    """Return required rerun safety flags."""

    return {
        "committed_binance_recent_data_only": True,
        "no_new_downloads": True,
        "no_network_calls": True,
        "no_threshold_change": True,
        "no_dr1_scope_expansion": True,
        "no_readiness_promotion": True,
        "research_only": True,
    }


def rerun_input_window() -> dict[str, object]:
    return {
        "source": "Binance public USDT-M Futures",
        "symbols": list(SYMBOLS),
        "timeframe": TIMEFRAME,
        "start_utc": RERUN_WINDOW_START.isoformat(),
        "end_utc": RERUN_WINDOW_END.isoformat(),
        "expected_rows_per_symbol": 1087,
        "source_validation_result": "DATA_REQUIREMENT_PASS",
    }


def _freshness_for_symbol(
    candles: Sequence[Candle],
    *,
    symbol: str,
    min_latest,
) -> dict[str, object]:
    ordered = sorted(candles, key=lambda item: item.timestamp)
    timestamps = [item.timestamp for item in ordered]
    duplicate_count = len(timestamps) - len(set(timestamps))
    monotonic = all(
        previous < current
        for previous, current in zip(timestamps, timestamps[1:], strict=False)
    )
    max_gap = _max_gap(ordered)
    gap_count = sum(
        1
        for previous, current in zip(ordered, ordered[1:], strict=False)
        if current.timestamp - previous.timestamp > EXPECTED_STEP
    )
    first = ordered[0].timestamp if ordered else None
    latest = ordered[-1].timestamp if ordered else None
    window_start = _subtract_months(latest, FRESHNESS_MIN_MONTHS) if latest else None
    sufficient = (
        first == RERUN_WINDOW_START
        and latest == RERUN_WINDOW_END
        and latest is not None
        and latest >= min_latest
        and window_start is not None
        and first <= window_start
        and max_gap is not None
        and max_gap <= EXPECTED_STEP
        and gap_count == 0
        and duplicate_count == 0
        and monotonic
    )
    return {
        "symbol": symbol,
        "sufficient": sufficient,
        "first_candle": first.isoformat() if first else None,
        "latest_candle": latest.isoformat() if latest else None,
        "expected_start": RERUN_WINDOW_START.isoformat(),
        "expected_end": RERUN_WINDOW_END.isoformat(),
        "contiguous_month_start": window_start.isoformat() if window_start else None,
        "window_candle_count": len(ordered),
        "max_gap_hours": (
            str(Decimal(str(max_gap.total_seconds())) / Decimal("3600"))
            if max_gap is not None
            else None
        ),
        "gap_count_above_expected_4h_step": gap_count,
        "duplicate_timestamp_count": duplicate_count,
        "timestamps_monotonic": monotonic,
        "latest_required_no_earlier_than": min_latest.isoformat(),
    }


def _validate_symbol_scope(candles_by_symbol: dict[str, Sequence[Candle]]) -> None:
    if sorted(candles_by_symbol) != sorted(SYMBOLS):
        raise ValueError(f"DR1 Binance recent rerun symbols must be exactly {list(SYMBOLS)}")
