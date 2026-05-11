"""Stage 54-SQ C8 direction-call agreement diagnostic.

Research-only. Re-derives Setup C direction calls from committed local CSVs
and compares Bitget vs Binance at symbol + rebalance timestamp alignment keys.
No network access, new downloads, gate changes, filters, or readiness claims.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from .candles import Candle, normalize_utc, parse_iso_utc
from .csv_loader import load_ohlcv_csv
from .setup_c_c7_expanded_validation import (
    DEV_WINDOW_END,
    DEV_WINDOW_START,
    FROZEN_SYMBOLS,
)
from .setup_c_tsmom import (
    PRIMARY_LOOKBACK,
    REBALANCE_BARS,
    TsmomInterval,
    _json_safe,
    build_tsmom_intervals,
)


REPORT_SCHEMA = "setup_c_c8_direction_agreement_report_v1"
DESIGN_LOCK = "docs/STAGE_54_SQ_C8_DIRECTION_CALL_AGREEMENT_DESIGN_LOCK.md"
HIGH_AGREEMENT_THRESHOLD = Decimal("0.80")
LOW_AGREEMENT_THRESHOLD = Decimal("0.60")
MATERIAL_MISSING_COVERAGE_THRESHOLD = Decimal("0.10")
MIN_ALIGNED_ROWS_PER_SYMBOL_WINDOW = 50
PRIMARY_INTERPRETATION_HIGH = "high_direction_agreement_magnitude_divergence"
PRIMARY_INTERPRETATION_LOW = "low_direction_agreement_signal_divergence"
PRIMARY_INTERPRETATION_MIXED = "mixed_or_inconclusive"
VENUES = ("bitget", "binance")
WINDOWS = ("development", "expanded", "combined")


@dataclass(frozen=True, slots=True)
class DirectionCall:
    """One re-derived direction call at a rebalance timestamp."""

    venue: str
    symbol: str
    timestamp: str
    window: str
    lookback: int
    direction: int


def normalize_timestamp_iso(value: datetime | str) -> str:
    """Normalize timestamps to UTC ISO-8601 for alignment."""

    timestamp = normalize_utc(value) if isinstance(value, datetime) else parse_iso_utc(value)
    return timestamp.isoformat()


def build_direction_calls(
    candles_by_symbol: dict[str, Sequence[Candle]],
    *,
    venue: str,
    window: str,
    lookback: int = PRIMARY_LOOKBACK,
) -> list[DirectionCall]:
    """Re-derive rebalance direction calls with the frozen Setup C detector."""

    intervals = build_tsmom_intervals(candles_by_symbol, lookback=lookback)
    return [
        DirectionCall(
            venue=venue,
            symbol=interval.symbol,
            timestamp=normalize_timestamp_iso(interval.timestamp),
            window=window,
            lookback=lookback,
            direction=interval.direction,
        )
        for interval in intervals
    ]


def evaluate_direction_agreement(
    bitget_calls: Sequence[DirectionCall],
    binance_calls: Sequence[DirectionCall],
    *,
    window: str,
    symbols: Sequence[str] = FROZEN_SYMBOLS,
    require_min_rows: bool = True,
) -> dict[str, object]:
    """Evaluate direction agreement for one window.

    Rows present in one venue but absent in the other are counted separately
    and excluded from agreement numerator and denominator.
    """

    bitget_by_symbol = _direction_map_by_symbol(bitget_calls)
    binance_by_symbol = _direction_map_by_symbol(binance_calls)
    symbol_results = {
        symbol: _agreement_summary(
            bitget_by_symbol.get(symbol, {}),
            binance_by_symbol.get(symbol, {}),
            symbol=symbol,
            window=window,
            require_min_rows=require_min_rows,
        )
        for symbol in symbols
    }
    all_symbols = _agreement_summary(
        _flatten_direction_maps(bitget_by_symbol, symbols),
        _flatten_direction_maps(binance_by_symbol, symbols),
        symbol="all_symbols",
        window=window,
        require_min_rows=False,
    )
    return {
        "window": window,
        "symbols": symbol_results,
        "all_symbols": all_symbols,
    }


def analyze_c8_direction_agreement(
    *,
    bitget_development_candles_by_symbol: dict[str, Sequence[Candle]],
    bitget_expanded_candles_by_symbol: dict[str, Sequence[Candle]],
    binance_development_candles_by_symbol: dict[str, Sequence[Candle]],
    binance_expanded_candles_by_symbol: dict[str, Sequence[Candle]],
) -> dict[str, object]:
    """Run the C8 diagnostic from committed candle inputs."""

    _reject_extra_symbol_keys(bitget_development_candles_by_symbol)
    _reject_extra_symbol_keys(bitget_expanded_candles_by_symbol)
    _reject_extra_symbol_keys(binance_development_candles_by_symbol)
    _reject_extra_symbol_keys(binance_expanded_candles_by_symbol)

    calls = {
        "bitget": {
            "development": build_direction_calls(
                bitget_development_candles_by_symbol,
                venue="bitget",
                window="development",
            ),
            "expanded": build_direction_calls(
                bitget_expanded_candles_by_symbol,
                venue="bitget",
                window="expanded",
            ),
        },
        "binance": {
            "development": build_direction_calls(
                binance_development_candles_by_symbol,
                venue="binance",
                window="development",
            ),
            "expanded": build_direction_calls(
                binance_expanded_candles_by_symbol,
                venue="binance",
                window="expanded",
            ),
        },
    }
    calls["bitget"]["combined"] = calls["bitget"]["development"] + calls["bitget"]["expanded"]
    calls["binance"]["combined"] = calls["binance"]["development"] + calls["binance"]["expanded"]

    windows = {
        window: evaluate_direction_agreement(
            calls["bitget"][window],
            calls["binance"][window],
            window=window,
        )
        for window in WINDOWS
    }

    report = {
        "schema": REPORT_SCHEMA,
        "design_lock": DESIGN_LOCK,
        "scope": "research_only_direction_call_agreement_diagnostic",
        "venues": list(VENUES),
        "symbols": list(FROZEN_SYMBOLS),
        "timeframe": "4H",
        "primary_lookback": PRIMARY_LOOKBACK,
        "sensitivity_lookbacks_reported": [],
        "sensitivity_policy": (
            "40-bar primary only; 20/60 not reported because the C8 primary "
            "comparison is 40-bar and no paired sensitivity direction artifact "
            "is required for this diagnostic"
        ),
        "rebalance_bars": REBALANCE_BARS,
        "windows": windows,
        "headline": {
            "development": windows["development"]["all_symbols"],
            "expanded": windows["expanded"]["all_symbols"],
            "combined": windows["combined"]["all_symbols"],
            "per_symbol_combined": windows["combined"]["symbols"],
        },
        "alignment_policy": {
            "key": "symbol + normalized UTC ISO-8601 rebalance timestamp",
            "timestamp_normalization": "UTC ISO-8601",
            "missing_row_policy": (
                "Rows present in one venue but absent in the other are counted "
                "as missing, excluded from agreement numerator and denominator, "
                "and reported as separate coverage counts."
            ),
            "mismatched_timestamp_formats": (
                "normalized before alignment; unresolved mismatches count as "
                "missing rows, not opposite direction calls"
            ),
            "combined_window": "development + expanded windows together",
        },
        "thresholds": {
            "high_agreement": str(HIGH_AGREEMENT_THRESHOLD),
            "low_agreement": str(LOW_AGREEMENT_THRESHOLD),
            "material_missing_coverage": str(MATERIAL_MISSING_COVERAGE_THRESHOLD),
            "minimum_aligned_rows_per_symbol_window": MIN_ALIGNED_ROWS_PER_SYMBOL_WINDOW,
        },
        "interpretation_labels": [
            PRIMARY_INTERPRETATION_HIGH,
            PRIMARY_INTERPRETATION_LOW,
            PRIMARY_INTERPRETATION_MIXED,
        ],
        "c7_inputs": {
            "bitget": "C7_PASS",
            "binance": "C7_PASS",
            "read_only": True,
        },
        "flags": _safety_flags(),
        "notes": [
            "Direction calls are re-derived from committed CSVs using the frozen Setup C detector.",
            "Headline report aggregates are not used as a direction-call source.",
            "C8 is observational only and does not alter C7 PASS verdicts.",
        ],
        "window_bounds": {
            "development_start": DEV_WINDOW_START.isoformat(),
            "development_end": DEV_WINDOW_END.isoformat(),
            "expanded_source": "committed C7 expanded CSVs",
        },
    }
    return _json_safe(report)  # type: ignore[return-value]


def load_committed_c8_candles(package_dir: Path | None = None) -> dict[str, dict[str, dict[str, list[Candle]]]]:
    """Load committed Bitget/Binance development and expanded CSVs."""

    root = package_dir or Path(__file__).resolve().parent
    data_root = root / "data"
    return {
        "bitget": {
            "development": _load_venue_window(data_root / "bitget"),
            "expanded": _load_venue_window(data_root / "bitget" / "expanded"),
        },
        "binance": {
            "development": _load_venue_window(data_root / "binance"),
            "expanded": _load_venue_window(data_root / "binance" / "expanded"),
        },
    }


def run_c8_direction_agreement(package_dir: Path | None = None) -> dict[str, object]:
    """Load committed data, run C8, and write deterministic artifacts."""

    root = package_dir or Path(__file__).resolve().parent
    candles = load_committed_c8_candles(root)
    report = analyze_c8_direction_agreement(
        bitget_development_candles_by_symbol=candles["bitget"]["development"],
        bitget_expanded_candles_by_symbol=candles["bitget"]["expanded"],
        binance_development_candles_by_symbol=candles["binance"]["development"],
        binance_expanded_candles_by_symbol=candles["binance"]["expanded"],
    )
    output_dir = root / "output" / "cross_venue"
    write_c8_artifacts(
        report,
        text_path=output_dir / "setup_c_c8_direction_agreement_report.txt",
        json_path=output_dir / "setup_c_c8_direction_agreement_report.json",
    )
    return report


def format_c8_report(report: dict[str, object]) -> str:
    """Format a deterministic text C8 report."""

    headline: dict[str, object] = report["headline"]  # type: ignore[assignment]
    lines = [
        "Setup C C8 direction-call agreement report",
        "",
        "Scope: research-only Bitget/Binance direction-call agreement diagnostic.",
        "No gate change, no filter introduced, no paper/runtime/trading/live readiness claim.",
        "",
        f"schema: {report['schema']}",
        f"primary_lookback: {report['primary_lookback']}",
        f"venues: {report['venues']}",
        f"symbols: {report['symbols']}",
        "",
        "Headline all-symbol agreement",
    ]
    for window in ("development", "expanded", "combined"):
        item: dict[str, object] = headline[window]  # type: ignore[assignment]
        lines.append(
            f"  {window}: agreement_pct={item['agreement_pct']}, "
            f"missing_coverage_pct={item['missing_coverage_pct']}, "
            f"aligned={item['aligned_row_count']}, "
            f"interpretation={item['interpretation_label']}"
        )
    lines.extend(["", "Per-symbol combined agreement"])
    per_symbol: dict[str, object] = headline["per_symbol_combined"]  # type: ignore[assignment]
    for symbol in FROZEN_SYMBOLS:
        item: dict[str, object] = per_symbol[symbol]  # type: ignore[assignment]
        lines.append(
            f"  {symbol}: agreement_pct={item['agreement_pct']}, "
            f"missing_coverage_pct={item['missing_coverage_pct']}, "
            f"aligned={item['aligned_row_count']}, "
            f"interpretation={item['interpretation_label']}"
        )
    lines.extend(
        [
            "",
            "Safety flags",
        ]
    )
    flags: dict[str, object] = report["flags"]  # type: ignore[assignment]
    for key in sorted(flags):
        lines.append(f"  {key}: {flags[key]}")
    return "\n".join(lines).rstrip() + "\n"


def write_c8_artifacts(
    report: dict[str, object],
    *,
    text_path: str | Path,
    json_path: str | Path,
) -> None:
    """Write deterministic C8 text and JSON artifacts."""

    text_output = Path(text_path)
    json_output = Path(json_path)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(format_c8_report(report), encoding="utf-8")
    json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _agreement_summary(
    bitget: dict[str, int],
    binance: dict[str, int],
    *,
    symbol: str,
    window: str,
    require_min_rows: bool,
) -> dict[str, object]:
    aligned_keys = sorted(set(bitget).intersection(binance))
    bitget_only = sorted(set(bitget) - set(binance))
    binance_only = sorted(set(binance) - set(bitget))
    matching = sum(1 for key in aligned_keys if bitget[key] == binance[key])
    opposite = sum(1 for key in aligned_keys if bitget[key] != binance[key])
    aligned = len(aligned_keys)
    missing = len(bitget_only) + len(binance_only)
    coverage_denominator = aligned + missing
    agreement = _ratio(matching, aligned)
    missing_coverage = _ratio(missing, coverage_denominator)
    insufficient_min_rows = require_min_rows and aligned < MIN_ALIGNED_ROWS_PER_SYMBOL_WINDOW
    material_missing = (
        missing_coverage is not None
        and missing_coverage > MATERIAL_MISSING_COVERAGE_THRESHOLD
    )
    return {
        "symbol": symbol,
        "window": window,
        "aligned_row_count": aligned,
        "matching_direction_count": matching,
        "opposite_direction_count": opposite,
        "bitget_only_missing_count": len(bitget_only),
        "binance_only_missing_count": len(binance_only),
        "total_coverage_denominator": coverage_denominator,
        "agreement_pct": _pct(agreement),
        "missing_coverage_pct": _pct(missing_coverage),
        "material_missing_coverage": material_missing,
        "insufficient_minimum_aligned_rows": insufficient_min_rows,
        "interpretation_label": classify_interpretation(
            agreement,
            missing_coverage=missing_coverage,
            aligned_row_count=aligned,
            require_min_rows=require_min_rows,
        ),
    }


def classify_interpretation(
    agreement: Decimal | None,
    *,
    missing_coverage: Decimal | None,
    aligned_row_count: int,
    require_min_rows: bool = True,
) -> str:
    """Classify C8 agreement using pre-registered thresholds."""

    if require_min_rows and aligned_row_count < MIN_ALIGNED_ROWS_PER_SYMBOL_WINDOW:
        return PRIMARY_INTERPRETATION_MIXED
    if (
        missing_coverage is not None
        and missing_coverage > MATERIAL_MISSING_COVERAGE_THRESHOLD
    ):
        return PRIMARY_INTERPRETATION_MIXED
    if agreement is None:
        return PRIMARY_INTERPRETATION_MIXED
    if agreement >= HIGH_AGREEMENT_THRESHOLD:
        return PRIMARY_INTERPRETATION_HIGH
    if agreement < LOW_AGREEMENT_THRESHOLD:
        return PRIMARY_INTERPRETATION_LOW
    return PRIMARY_INTERPRETATION_MIXED


def _direction_map_by_symbol(
    calls: Sequence[DirectionCall],
) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for call in calls:
        output.setdefault(call.symbol, {})[normalize_timestamp_iso(call.timestamp)] = call.direction
    return output


def _flatten_direction_maps(
    by_symbol: dict[str, dict[str, int]],
    symbols: Sequence[str],
) -> dict[str, int]:
    return {
        f"{symbol}|{timestamp}": direction
        for symbol in symbols
        for timestamp, direction in by_symbol.get(symbol, {}).items()
    }


def _load_venue_window(directory: Path) -> dict[str, list[Candle]]:
    return {
        symbol: load_ohlcv_csv(directory / f"{symbol}_USDT-FUTURES_4H.csv")
        for symbol in FROZEN_SYMBOLS
    }


def _reject_extra_symbol_keys(by_symbol: dict[str, object]) -> None:
    extras = sorted(set(by_symbol) - set(FROZEN_SYMBOLS))
    if extras:
        raise ValueError(f"unexpected symbol keys: {extras}")


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def _pct(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value * Decimal("100"))


def _safety_flags() -> dict[str, bool]:
    return {
        "observational_only": True,
        "c7_verdicts_read_only": True,
        "no_gate_change": True,
        "no_filter_introduced": True,
        "no_readiness_promotion": True,
        "no_new_downloads": True,
    }
