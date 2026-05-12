"""Stage 54-SQ DR1 data recency / predictability reconnaissance.

Research-only diagnostic over committed local Bitget/Binance 4H CSV artifacts.
No network access, downloads, data mutation, strategy filters, or readiness
claims are introduced here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle, normalize_utc, parse_iso_utc
from .csv_loader import load_ohlcv_csv
from .setup_c_c7_expanded_validation import FROZEN_SYMBOLS
from .setup_c_tsmom import (
    PRIMARY_COST_SCENARIO,
    PRIMARY_LOOKBACK,
    REBALANCE_BARS,
    _json_safe,
    build_tsmom_intervals,
    summarize_intervals,
)


REPORT_SCHEMA = "setup_c_dr1_data_recency_predictability_report_v1"
DESIGN_LOCK = "docs/STAGE_54_SQ_DR1_DATA_RECENCY_PREDICTABILITY_DESIGN_LOCK.md"
IMPLEMENTATION_DATE = parse_iso_utc("2026-05-12T00:00:00+00:00")
VENUES = ("bitget", "binance")
SYMBOLS = FROZEN_SYMBOLS
TIMEFRAME = "4H"
FOUR_HOURS = timedelta(hours=4)
FRESHNESS_MIN_MONTHS = 6
FRESHNESS_MAX_AGE_DAYS = 30
MIN_NON_OVERLAPPING_OBSERVATIONS = 20
LEAD_LAG_SUPPORTIVE_THRESHOLD = Decimal("0.60")
AUTOCORR_SUPPORTIVE_THRESHOLD = Decimal("0.52")
AUTOCORR_WEAK_THRESHOLD = Decimal("0.48")
VARIANCE_RATIO_SUPPORTIVE_THRESHOLD = Decimal("1.05")
VARIANCE_RATIO_WEAK_THRESHOLD = Decimal("0.95")
OUTCOME_HIGH = "HIGH"
OUTCOME_LOW = "LOW"
OUTCOME_INCONCLUSIVE = "INCONCLUSIVE"
ANALYSIS_SUPPORTIVE = "supportive"
ANALYSIS_WEAK = "weak"
ANALYSIS_INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class BlockReturn:
    """One non-overlapping return block."""

    symbol: str
    timestamp: datetime
    value: Decimal


def analyze_dr1_data_recency_predictability(
    candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]],
    *,
    implementation_date: datetime | str = IMPLEMENTATION_DATE,
) -> dict[str, object]:
    """Run DR1 from committed candle inputs."""

    implementation_dt = _coerce_utc(implementation_date)
    _validate_scope(candles_by_venue_symbol)

    freshness = evaluate_freshness(
        candles_by_venue_symbol,
        implementation_date=implementation_dt,
    )
    recent_candles = _recent_candles_by_venue_symbol(candles_by_venue_symbol)
    autocorrelation = analyze_non_overlapping_autocorrelation(recent_candles)
    variance_ratio = analyze_variance_ratio(recent_candles)
    lead_lag = analyze_btc_lead_lag(recent_candles)
    persistence = analyze_setup_c_recent_persistence(recent_candles)
    analyses = {
        "non_overlapping_return_autocorrelation": autocorrelation,
        "variance_ratio_predictability": variance_ratio,
        "btc_to_eth_sol_lead_lag": lead_lag,
        "setup_c_recent_out_of_window_persistence": persistence,
    }
    decision = classify_dr1_outcome(
        freshness_eligible=bool(freshness["eligible"]),
        analyses=analyses,
    )
    missing_data_requirement = _missing_data_requirement(
        freshness,
        implementation_date=implementation_dt,
    )

    report = {
        "schema": REPORT_SCHEMA,
        "design_lock": DESIGN_LOCK,
        "scope": "research_only_data_recency_predictability_reconnaissance",
        "implementation_date": implementation_dt.isoformat(),
        "venues": list(VENUES),
        "symbols": list(SYMBOLS),
        "timeframe": TIMEFRAME,
        "primary_lookback": PRIMARY_LOOKBACK,
        "rebalance_bars": REBALANCE_BARS,
        "dr1_decision": decision,
        "freshness_eligibility": freshness,
        "analyses": analyses,
        "missing_data_requirement": missing_data_requirement,
        "interpretation_rules": {
            "freshness": (
                "at least 6 contiguous months of committed 4H candles ending "
                "no earlier than 30 calendar days before implementation date"
            ),
            "lead_lag_supportive": (
                "BTC -> ETH/SOL directional agreement must exceed 60% on "
                "non-overlapping bars; <=60% or underpowered coverage is "
                "inconclusive"
            ),
            "high": (
                "freshness eligible, predictability checks supportive, and "
                "frozen Setup C recent/out-of-window behavior does not "
                "contradict C7 evidence"
            ),
            "low": "freshness or predictability materially weaken current evidence",
            "inconclusive": "missing, underpowered, or mixed evidence",
        },
        "decision_implication": _decision_implication(decision),
        "flags": safety_flags(),
    }
    return _json_safe(report)  # type: ignore[return-value]


def evaluate_freshness(
    candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]],
    *,
    implementation_date: datetime | str,
) -> dict[str, object]:
    """Evaluate locked DR1 freshness coverage."""

    implementation_dt = _coerce_utc(implementation_date)
    min_latest = implementation_dt - timedelta(days=FRESHNESS_MAX_AGE_DAYS)
    per_series: dict[str, dict[str, object]] = {}
    eligible = True
    for venue in VENUES:
        per_series[venue] = {}
        for symbol in SYMBOLS:
            summary = _freshness_for_series(
                list(candles_by_venue_symbol[venue][symbol]),
                implementation_date=implementation_dt,
                min_latest=min_latest,
            )
            eligible = eligible and bool(summary["sufficient"])
            per_series[venue][symbol] = summary
    return {
        "eligible": eligible,
        "implementation_date": implementation_dt.isoformat(),
        "minimum_latest_candle": min_latest.isoformat(),
        "minimum_contiguous_months": FRESHNESS_MIN_MONTHS,
        "per_series": per_series,
    }


def analyze_non_overlapping_autocorrelation(
    candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]],
) -> dict[str, object]:
    """Evaluate same-sign persistence across adjacent non-overlapping returns."""

    pooled_matches = 0
    pooled_observations = 0
    per_series: dict[str, dict[str, object]] = {}
    for venue in VENUES:
        per_series[venue] = {}
        for symbol in SYMBOLS:
            blocks = non_overlapping_block_returns(
                candles_by_venue_symbol[venue][symbol],
                symbol=symbol,
            )
            signs = [_sign(block.value) for block in blocks if _sign(block.value) != 0]
            matches, observations = _adjacent_same_sign_counts(signs)
            pooled_matches += matches
            pooled_observations += observations
            rate = _ratio(matches, observations)
            per_series[venue][symbol] = {
                "observations": observations,
                "same_sign_count": matches,
                "same_sign_rate": _decimal_string(rate),
                "outcome": _classify_autocorr(rate, observations),
            }
    pooled_rate = _ratio(pooled_matches, pooled_observations)
    return {
        "method": (
            "adjacent same-sign rate over non-overlapping 40-bar returns, "
            "using committed recent candles only"
        ),
        "pooled_observations": pooled_observations,
        "pooled_same_sign_count": pooled_matches,
        "pooled_same_sign_rate": _decimal_string(pooled_rate),
        "outcome": _classify_autocorr(pooled_rate, pooled_observations),
        "per_series": per_series,
        "thresholds": {
            "supportive_gt": str(AUTOCORR_SUPPORTIVE_THRESHOLD),
            "weak_lt": str(AUTOCORR_WEAK_THRESHOLD),
            "minimum_observations": MIN_NON_OVERLAPPING_OBSERVATIONS,
        },
    }


def analyze_variance_ratio(
    candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]],
) -> dict[str, object]:
    """Evaluate a simple variance-ratio style persistence check."""

    short_returns: list[Decimal] = []
    long_returns: list[Decimal] = []
    for venue in VENUES:
        for symbol in SYMBOLS:
            candles = list(candles_by_venue_symbol[venue][symbol])
            short_returns.extend(_step_returns(candles, step=1))
            long_returns.extend(_non_overlapping_values(candles, step=PRIMARY_LOOKBACK))

    short_var = _sample_variance(short_returns)
    long_var = _sample_variance(long_returns)
    ratio = None
    if short_var is not None and short_var > Decimal("0") and long_var is not None:
        ratio = long_var / (short_var * Decimal(PRIMARY_LOOKBACK))
    observations = min(len(short_returns), len(long_returns))
    outcome = _classify_variance_ratio(ratio, observations)
    return {
        "method": (
            "variance of non-overlapping 40-bar returns divided by 40 times "
            "one-bar return variance"
        ),
        "short_return_observations": len(short_returns),
        "long_return_observations": len(long_returns),
        "variance_ratio": _decimal_string(ratio),
        "outcome": outcome,
        "thresholds": {
            "supportive_gt": str(VARIANCE_RATIO_SUPPORTIVE_THRESHOLD),
            "weak_lt": str(VARIANCE_RATIO_WEAK_THRESHOLD),
            "minimum_long_observations": MIN_NON_OVERLAPPING_OBSERVATIONS,
        },
    }


def analyze_btc_lead_lag(
    candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]],
) -> dict[str, object]:
    """Evaluate BTC one-block lead directional agreement for ETH/SOL."""

    matches = 0
    observations = 0
    per_target: dict[str, dict[str, object]] = {}
    for target in ("ETHUSDT", "SOLUSDT"):
        target_matches = 0
        target_observations = 0
        for venue in VENUES:
            btc = non_overlapping_block_returns(
                candles_by_venue_symbol[venue]["BTCUSDT"],
                symbol="BTCUSDT",
            )
            alt = non_overlapping_block_returns(
                candles_by_venue_symbol[venue][target],
                symbol=target,
            )
            btc_by_time = {block.timestamp: _sign(block.value) for block in btc}
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
    candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]],
) -> dict[str, object]:
    """Re-evaluate frozen Setup C behavior on the committed recent segment."""

    per_venue: dict[str, dict[str, object]] = {}
    weak_venues = 0
    supportive_venues = 0
    for venue in VENUES:
        intervals = build_tsmom_intervals(
            candles_by_venue_symbol[venue],
            lookback=PRIMARY_LOOKBACK,
        )
        summary = summarize_intervals(intervals)
        vt_post_cost = Decimal(
            str(
                summary["volatility_targeted_post_cost_return"][PRIMARY_COST_SCENARIO]  # type: ignore[index]
            )
        )
        per_symbol = {}
        non_negative_symbols = 0
        for symbol in SYMBOLS:
            symbol_intervals = [item for item in intervals if item.symbol == symbol]
            symbol_summary = summarize_intervals(symbol_intervals)
            symbol_value = Decimal(
                str(
                    symbol_summary["volatility_targeted_post_cost_return"][
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
            supportive_venues += 1
        else:
            outcome = ANALYSIS_WEAK
            weak_venues += 1
        per_venue[venue] = {
            "intervals": len(intervals),
            "vt_post_cost_moderate": str(vt_post_cost),
            "non_negative_symbols": non_negative_symbols,
            "outcome": outcome,
            "per_symbol": per_symbol,
        }

    if weak_venues:
        outcome = ANALYSIS_WEAK
    elif supportive_venues == len(VENUES):
        outcome = ANALYSIS_SUPPORTIVE
    else:
        outcome = ANALYSIS_INCONCLUSIVE
    return {
        "method": (
            "frozen Setup C 40-bar volatility-targeted post-cost moderate "
            "on committed recent six-month segment"
        ),
        "outcome": outcome,
        "per_venue": per_venue,
    }


def classify_lead_lag(agreement: Decimal | None, observations: int) -> str:
    """Classify lead-lag with the locked >60% supportive rule."""

    if observations < MIN_NON_OVERLAPPING_OBSERVATIONS or agreement is None:
        return ANALYSIS_INCONCLUSIVE
    if agreement > LEAD_LAG_SUPPORTIVE_THRESHOLD:
        return ANALYSIS_SUPPORTIVE
    return ANALYSIS_INCONCLUSIVE


def classify_dr1_outcome(
    *,
    freshness_eligible: bool,
    analyses: dict[str, dict[str, object]],
) -> str:
    """Classify DR1 using the design-lock HIGH / LOW / INCONCLUSIVE map."""

    if not freshness_eligible:
        return OUTCOME_INCONCLUSIVE
    outcomes = [str(item["outcome"]) for item in analyses.values()]
    if ANALYSIS_WEAK in outcomes:
        return OUTCOME_LOW
    if outcomes and all(outcome == ANALYSIS_SUPPORTIVE for outcome in outcomes):
        return OUTCOME_HIGH
    return OUTCOME_INCONCLUSIVE


def non_overlapping_block_returns(
    candles: Sequence[Candle],
    *,
    symbol: str,
    step: int = PRIMARY_LOOKBACK,
) -> list[BlockReturn]:
    """Return close-to-close non-overlapping block returns."""

    blocks: list[BlockReturn] = []
    ordered = sorted(candles, key=lambda item: item.timestamp)
    for index in range(step, len(ordered), step):
        previous_close = ordered[index - step].close
        if previous_close <= Decimal("0"):
            continue
        blocks.append(
            BlockReturn(
                symbol=symbol,
                timestamp=ordered[index].timestamp,
                value=(ordered[index].close / previous_close) - Decimal("1"),
            )
        )
    return blocks


def load_committed_dr1_candles(
    package_dir: Path | None = None,
) -> dict[str, dict[str, list[Candle]]]:
    """Load committed Bitget/Binance development and expanded CSV artifacts."""

    root = package_dir or Path(__file__).resolve().parent
    data_root = root / "data"
    output: dict[str, dict[str, list[Candle]]] = {}
    for venue in VENUES:
        output[venue] = {}
        for symbol in SYMBOLS:
            development = load_ohlcv_csv(
                data_root / venue / f"{symbol}_USDT-FUTURES_4H.csv"
            )
            expanded = load_ohlcv_csv(
                data_root / venue / "expanded" / f"{symbol}_USDT-FUTURES_4H.csv"
            )
            by_timestamp = {candle.timestamp: candle for candle in development + expanded}
            output[venue][symbol] = [
                by_timestamp[timestamp] for timestamp in sorted(by_timestamp)
            ]
    return output


def run_dr1_data_recency_predictability(
    package_dir: Path | None = None,
) -> dict[str, object]:
    """Load committed data, run DR1, and write deterministic artifacts."""

    root = package_dir or Path(__file__).resolve().parent
    candles = load_committed_dr1_candles(root)
    report = analyze_dr1_data_recency_predictability(candles)
    output_dir = root / "output" / "recon"
    write_dr1_artifacts(
        report,
        text_path=output_dir / "setup_c_dr1_data_recency_predictability_report.txt",
        json_path=output_dir / "setup_c_dr1_data_recency_predictability_report.json",
    )
    return report


def format_dr1_report(report: dict[str, object]) -> str:
    """Format a deterministic DR1 text report."""

    freshness: dict[str, object] = report["freshness_eligibility"]  # type: ignore[assignment]
    analyses: dict[str, object] = report["analyses"]  # type: ignore[assignment]
    lines = [
        "Setup C DR1 data recency / predictability reconnaissance report",
        "",
        "Scope: research-only committed Bitget/Binance 4H CSV artifacts.",
        "No downloads, no gate change, no filter, no paper/runtime/trading/live readiness.",
        "",
        f"schema: {report['schema']}",
        f"decision: {report['dr1_decision']}",
        f"freshness_eligible: {freshness['eligible']}",
        f"implementation_date: {report['implementation_date']}",
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
    lines.extend(
        [
            "",
            f"missing_data_requirement: {report['missing_data_requirement']}",
            "",
            "Safety flags",
        ]
    )
    flags: dict[str, object] = report["flags"]  # type: ignore[assignment]
    for key in sorted(flags):
        lines.append(f"  {key}: {flags[key]}")
    return "\n".join(lines).rstrip() + "\n"


def write_dr1_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic DR1 text and JSON artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_dr1_report(report), encoding="utf-8")
    json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def safety_flags() -> dict[str, bool]:
    """Return required DR1 safety flags."""

    return {
        "no_new_downloads": True,
        "observational_only": True,
        "no_readiness_promotion": True,
        "no_gate_change": True,
        "no_filter_introduced": True,
        "research_only": True,
    }


def _freshness_for_series(
    candles: Sequence[Candle],
    *,
    implementation_date: datetime,
    min_latest: datetime,
) -> dict[str, object]:
    ordered = sorted(candles, key=lambda item: item.timestamp)
    if not ordered:
        return {
            "sufficient": False,
            "reason": "no committed candles",
            "first_candle": None,
            "latest_candle": None,
            "contiguous_month_start": None,
            "window_candle_count": 0,
            "max_gap_hours": None,
        }
    latest = ordered[-1].timestamp
    window_start = _subtract_months(latest, FRESHNESS_MIN_MONTHS)
    window = [candle for candle in ordered if window_start <= candle.timestamp <= latest]
    max_gap = _max_gap(window)
    latest_recent_enough = latest >= min_latest
    enough_history = ordered[0].timestamp <= window_start
    contiguous = max_gap is not None and max_gap <= FOUR_HOURS
    sufficient = latest_recent_enough and enough_history and contiguous
    reasons: list[str] = []
    if not latest_recent_enough:
        reasons.append("latest candle is older than freshness cutoff")
    if not enough_history:
        reasons.append("less than six months of committed candle history")
    if not contiguous:
        reasons.append("six-month window is not contiguous at 4H cadence")
    return {
        "sufficient": sufficient,
        "reason": "sufficient" if sufficient else "; ".join(reasons),
        "first_candle": ordered[0].timestamp.isoformat(),
        "latest_candle": latest.isoformat(),
        "contiguous_month_start": window_start.isoformat(),
        "window_candle_count": len(window),
        "max_gap_hours": (
            str(Decimal(str(max_gap.total_seconds())) / Decimal("3600"))
            if max_gap is not None
            else None
        ),
        "latest_required_no_earlier_than": min_latest.isoformat(),
    }


def _recent_candles_by_venue_symbol(
    candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]],
) -> dict[str, dict[str, list[Candle]]]:
    recent: dict[str, dict[str, list[Candle]]] = {}
    for venue in VENUES:
        recent[venue] = {}
        for symbol in SYMBOLS:
            candles = sorted(candles_by_venue_symbol[venue][symbol], key=lambda item: item.timestamp)
            if not candles:
                recent[venue][symbol] = []
                continue
            latest = candles[-1].timestamp
            start = _subtract_months(latest, FRESHNESS_MIN_MONTHS)
            recent[venue][symbol] = [
                candle for candle in candles if start <= candle.timestamp <= latest
            ]
    return recent


def _missing_data_requirement(
    freshness: dict[str, object],
    *,
    implementation_date: datetime,
) -> str | None:
    if freshness["eligible"]:
        return None
    min_latest = implementation_date - timedelta(days=FRESHNESS_MAX_AGE_DAYS)
    return (
        "Committed Bitget and Binance BTCUSDT/ETHUSDT/SOLUSDT 4H CSV artifacts "
        f"must each contain at least {FRESHNESS_MIN_MONTHS} contiguous months of "
        f"candles ending no earlier than {min_latest.isoformat()} before DR1 can "
        "support a paper-candidate design-lock discussion."
    )


def _decision_implication(decision: str) -> str:
    if decision == OUTCOME_HIGH:
        return (
            "Future paper-candidate design lock may be considered only if the "
            "owner explicitly chooses to continue."
        )
    if decision == OUTCOME_LOW:
        return "Park Setup C or trigger structural review before paper-candidate design lock."
    return "Define the missing or underpowered evidence; do not proceed to paper-candidate design lock."


def _classify_autocorr(rate: Decimal | None, observations: int) -> str:
    if observations < MIN_NON_OVERLAPPING_OBSERVATIONS or rate is None:
        return ANALYSIS_INCONCLUSIVE
    if rate > AUTOCORR_SUPPORTIVE_THRESHOLD:
        return ANALYSIS_SUPPORTIVE
    if rate < AUTOCORR_WEAK_THRESHOLD:
        return ANALYSIS_WEAK
    return ANALYSIS_INCONCLUSIVE


def _classify_variance_ratio(ratio: Decimal | None, observations: int) -> str:
    if observations < MIN_NON_OVERLAPPING_OBSERVATIONS or ratio is None:
        return ANALYSIS_INCONCLUSIVE
    if ratio > VARIANCE_RATIO_SUPPORTIVE_THRESHOLD:
        return ANALYSIS_SUPPORTIVE
    if ratio < VARIANCE_RATIO_WEAK_THRESHOLD:
        return ANALYSIS_WEAK
    return ANALYSIS_INCONCLUSIVE


def _step_returns(candles: Sequence[Candle], *, step: int) -> list[Decimal]:
    ordered = sorted(candles, key=lambda item: item.timestamp)
    returns: list[Decimal] = []
    for index in range(step, len(ordered)):
        previous_close = ordered[index - step].close
        if previous_close <= Decimal("0"):
            continue
        returns.append((ordered[index].close / previous_close) - Decimal("1"))
    return returns


def _non_overlapping_values(candles: Sequence[Candle], *, step: int) -> list[Decimal]:
    return [
        block.value
        for block in non_overlapping_block_returns(candles, symbol="pooled", step=step)
    ]


def _sample_variance(values: Sequence[Decimal]) -> Decimal | None:
    if len(values) < 2:
        return None
    average = sum(values, Decimal("0")) / Decimal(len(values))
    return sum(((value - average) * (value - average) for value in values), Decimal("0")) / Decimal(len(values) - 1)


def _adjacent_same_sign_counts(signs: Sequence[int]) -> tuple[int, int]:
    matches = 0
    observations = 0
    for previous, current in zip(signs, signs[1:], strict=False):
        observations += 1
        if previous == current:
            matches += 1
    return matches, observations


def _sign(value: Decimal) -> int:
    if value > Decimal("0"):
        return 1
    if value < Decimal("0"):
        return -1
    return 0


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def _decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _max_gap(candles: Sequence[Candle]) -> timedelta | None:
    if len(candles) < 2:
        return None
    ordered = sorted(candles, key=lambda item: item.timestamp)
    return max(
        current.timestamp - previous.timestamp
        for previous, current in zip(ordered, ordered[1:], strict=False)
    )


def _subtract_months(timestamp: datetime, months: int) -> datetime:
    month_index = timestamp.month - 1 - months
    year = timestamp.year + month_index // 12
    month = month_index % 12 + 1
    day = min(timestamp.day, _days_in_month(year, month))
    return timestamp.replace(year=year, month=month, day=day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=UTC)
    this_month = datetime(year, month, 1, tzinfo=UTC)
    return (next_month - this_month).days


def _coerce_utc(value: datetime | str) -> datetime:
    return normalize_utc(value) if isinstance(value, datetime) else parse_iso_utc(value)


def _validate_scope(candles_by_venue_symbol: dict[str, dict[str, Sequence[Candle]]]) -> None:
    if sorted(candles_by_venue_symbol) != sorted(VENUES):
        raise ValueError(f"DR1 venues must be exactly {list(VENUES)}")
    for venue in VENUES:
        if sorted(candles_by_venue_symbol[venue]) != sorted(SYMBOLS):
            raise ValueError(f"{venue}: DR1 symbols must be exactly {list(SYMBOLS)}")
