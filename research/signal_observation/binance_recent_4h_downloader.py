"""Bounded Binance recent 4H acquisition and validation for DR1 freshness.

This module is limited to the approved Binance public USDT-M Futures kline
path, BTCUSDT/ETHUSDT/SOLUSDT, and 4H candles. It downloads only when the
runner invokes the acquisition path; validation helpers are deterministic and
side-effect free apart from writing the requested artifacts.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Callable, Sequence

from .binance_public_downloader import (
    BINANCE_FUTURES_KLINES_URL,
    download_binance_futures_klines,
)
from .candles import normalize_utc, parse_iso_utc
from .setup_c_tsmom import _json_safe


SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
INTERVAL = "4h"
TIMEFRAME = "4H"
EXPECTED_STEP = timedelta(hours=4)
RECENT_MONTHS = 6
RESULT_PASS = "DATA_REQUIREMENT_PASS"
RESULT_FAIL = "DATA_REQUIREMENT_FAIL"
RESULT_BLOCKED = "DATA_ACQUISITION_BLOCKED"
REPORT_SCHEMA = "setup_c_dr1_binance_recent_4h_acquisition_v1"
DESIGN_LOCK = "docs/STAGE_54_SQ_DR1_BINANCE_RECENT_DATA_ACQUISITION_DESIGN_LOCK.md"
DEFAULT_DATA_DIR = Path("research/signal_observation/data/binance_recent")
DEFAULT_OUTPUT_DIR = Path("research/signal_observation/output/binance_recent")
REPORT_JSON_NAME = "setup_c_dr1_binance_recent_4h_acquisition_report.json"
REPORT_TXT_NAME = "setup_c_dr1_binance_recent_4h_acquisition_report.txt"


@dataclass(frozen=True, slots=True)
class LockedWindow:
    """Immutable acquisition target window locked before any request."""

    acquisition_task_started_utc: datetime
    locked_window_start_utc: datetime
    locked_window_end_utc: datetime

    def as_report(self) -> dict[str, str]:
        return {
            "acquisition_task_started_utc": _iso(self.acquisition_task_started_utc),
            "locked_window_start_utc": _iso(self.locked_window_start_utc),
            "locked_window_end_utc": _iso(self.locked_window_end_utc),
        }


FetchKlines = Callable[[str, LockedWindow, Path], Path]


def create_locked_window(task_started_utc: datetime | None = None) -> LockedWindow:
    """Create the fixed six-month target window before any network request."""

    started = normalize_utc(task_started_utc or datetime.now(tz=UTC))
    end = latest_completed_4h_open(started)
    start = subtract_months(end, RECENT_MONTHS)
    return LockedWindow(
        acquisition_task_started_utc=started,
        locked_window_start_utc=start,
        locked_window_end_utc=end,
    )


def latest_completed_4h_open(now_utc: datetime) -> datetime:
    """Return the open timestamp of the latest fully completed 4H candle."""

    now = normalize_utc(now_utc)
    floored_hour = now.hour - (now.hour % 4)
    boundary = now.replace(hour=floored_hour, minute=0, second=0, microsecond=0)
    return boundary - EXPECTED_STEP


def run_binance_recent_4h_acquisition(
    *,
    locked_window: LockedWindow | None = None,
    data_dir: str | Path = DEFAULT_DATA_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    fetcher: FetchKlines | None = None,
) -> dict[str, object]:
    """Acquire the locked Binance window and write validation artifacts."""

    window = locked_window or create_locked_window()
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)
    fetch = fetcher or fetch_symbol_window
    errors: dict[str, str] = {}
    csv_paths: dict[str, str] = {}

    for symbol in SYMBOLS:
        csv_path = data_path / output_csv_name(symbol)
        try:
            fetch(symbol, window, csv_path)
        except Exception as exc:  # noqa: BLE001 - report bounded acquisition blocker
            errors[symbol] = f"{type(exc).__name__}: {exc}"
            continue
        csv_paths[symbol] = str(csv_path)

    if errors:
        per_symbol = {
            symbol: blocked_symbol_report(symbol, window, errors.get(symbol))
            for symbol in SYMBOLS
        }
        result = RESULT_BLOCKED
    else:
        per_symbol = {
            symbol: validate_symbol_csv(Path(csv_paths[symbol]), symbol, window)
            for symbol in SYMBOLS
        }
        result = classify_acquisition_result(per_symbol.values(), blocked=False)

    report = build_validation_report(
        locked_window=window,
        result=result,
        per_symbol=per_symbol,
        csv_paths=csv_paths,
        errors=errors,
    )
    write_validation_artifacts(report, output_path)
    return report


def fetch_symbol_window(symbol: str, window: LockedWindow, output_csv: Path) -> Path:
    """Download one approved Binance USDT-M Futures 4H symbol window."""

    validate_symbol_scope(symbol)
    return download_binance_futures_klines(
        symbol=symbol,
        interval=INTERVAL,
        output_csv=output_csv,
        limit=1500,
        start_time=to_epoch_ms(window.locked_window_start_utc),
        end_time=to_epoch_ms(window.locked_window_end_utc),
        max_pages=3,
    )


def validate_symbol_scope(symbol: str) -> None:
    if symbol not in SYMBOLS:
        raise ValueError(f"symbol must be one of {SYMBOLS}")


def validate_symbol_csv(
    csv_path: Path,
    symbol: str,
    locked_window: LockedWindow,
) -> dict[str, object]:
    """Validate one downloaded CSV against the locked DR1 data requirement."""

    validate_symbol_scope(symbol)
    rows = read_timestamp_rows(csv_path)
    timestamps = [row["timestamp"] for row in rows]
    duplicate_count = len(timestamps) - len(set(timestamps))
    monotonic = all(
        previous < current
        for previous, current in zip(timestamps, timestamps[1:], strict=False)
    )
    gaps = [
        current - previous
        for previous, current in zip(timestamps, timestamps[1:], strict=False)
    ]
    max_gap = max(gaps) if gaps else None
    gap_count = sum(1 for gap in gaps if gap > EXPECTED_STEP)
    first = timestamps[0] if timestamps else None
    last = timestamps[-1] if timestamps else None
    start_matches = first == locked_window.locked_window_start_utc
    end_matches = last == locked_window.locked_window_end_utc
    contiguous = bool(rows) and monotonic and duplicate_count == 0 and gap_count == 0
    requirement_pass = contiguous and start_matches and end_matches

    return {
        "symbol": symbol,
        "csv_path": str(csv_path),
        "row_count": len(rows),
        "first_timestamp": _iso(first),
        "last_timestamp": _iso(last),
        "expected_locked_start": _iso(locked_window.locked_window_start_utc),
        "expected_locked_end": _iso(locked_window.locked_window_end_utc),
        "timestamps_monotonic": monotonic,
        "duplicate_timestamp_count": duplicate_count,
        "max_gap": format_timedelta(max_gap),
        "max_gap_hours": decimal_hours(max_gap),
        "gap_count_above_expected_4h_step": gap_count,
        "contiguity_pass": contiguous,
        "recent_window_requirement_pass": requirement_pass,
    }


def read_timestamp_rows(csv_path: Path) -> list[dict[str, datetime]]:
    """Read timestamp rows while preserving duplicates for validation."""

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path}: CSV file is empty")
        normalized_headers = {name.strip().lower() for name in reader.fieldnames}
        if "timestamp" not in normalized_headers:
            raise ValueError(f"{csv_path}: missing timestamp column")
        rows: list[dict[str, datetime]] = []
        for row_number, row in enumerate(reader, start=2):
            timestamp_text = row.get("timestamp") or row.get("Timestamp") or ""
            rows.append({"timestamp": parse_iso_utc(timestamp_text)})
    return rows


def classify_acquisition_result(
    per_symbol: Sequence[dict[str, object]],
    *,
    blocked: bool,
) -> str:
    """Classify the bounded acquisition result."""

    if blocked:
        return RESULT_BLOCKED
    if all(bool(summary.get("recent_window_requirement_pass")) for summary in per_symbol):
        return RESULT_PASS
    return RESULT_FAIL


def blocked_symbol_report(
    symbol: str,
    locked_window: LockedWindow,
    error: str | None,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "row_count": 0,
        "first_timestamp": None,
        "last_timestamp": None,
        "expected_locked_start": _iso(locked_window.locked_window_start_utc),
        "expected_locked_end": _iso(locked_window.locked_window_end_utc),
        "timestamps_monotonic": False,
        "duplicate_timestamp_count": 0,
        "max_gap": None,
        "max_gap_hours": None,
        "gap_count_above_expected_4h_step": None,
        "contiguity_pass": False,
        "recent_window_requirement_pass": False,
        "error": error or "not attempted after another symbol blocked",
    }


def build_validation_report(
    *,
    locked_window: LockedWindow,
    result: str,
    per_symbol: dict[str, dict[str, object]],
    csv_paths: dict[str, str],
    errors: dict[str, str],
) -> dict[str, object]:
    """Build the deterministic acquisition validation report."""

    report = {
        "schema": REPORT_SCHEMA,
        "design_lock": DESIGN_LOCK,
        "source": {
            "venue": "binance_usdt_m_futures",
            "public_endpoint": BINANCE_FUTURES_KLINES_URL,
            "interval": INTERVAL,
            "timeframe": TIMEFRAME,
            "symbols": list(SYMBOLS),
        },
        "locked_window": locked_window.as_report(),
        "result": result,
        "decision_implication": decision_implication(result),
        "per_symbol": per_symbol,
        "csv_paths": csv_paths,
        "errors": errors,
        "flags": safety_flags(),
    }
    return _json_safe(report)  # type: ignore[return-value]


def write_validation_artifacts(report: dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON_NAME
    txt_path = output_dir / REPORT_TXT_NAME
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    txt_path.write_text(format_validation_report(report), encoding="utf-8")


def format_validation_report(report: dict[str, object]) -> str:
    locked = report["locked_window"]
    assert isinstance(locked, dict)
    lines = [
        "Setup C DR1 Binance Recent 4H Acquisition Validation",
        "",
        f"Result: {report['result']}",
        f"Task started UTC: {locked['acquisition_task_started_utc']}",
        f"Locked window start UTC: {locked['locked_window_start_utc']}",
        f"Locked window end UTC: {locked['locked_window_end_utc']}",
        "",
        "Per-symbol validation:",
    ]
    per_symbol = report["per_symbol"]
    assert isinstance(per_symbol, dict)
    for symbol in SYMBOLS:
        summary = per_symbol[symbol]
        assert isinstance(summary, dict)
        lines.extend(
            [
                f"- {symbol}:",
                f"  rows: {summary['row_count']}",
                f"  first/last: {summary['first_timestamp']} / {summary['last_timestamp']}",
                f"  max gap: {summary['max_gap']}",
                f"  gap count > 4H: {summary['gap_count_above_expected_4h_step']}",
                f"  contiguity: {'PASS' if summary['contiguity_pass'] else 'FAIL'}",
                (
                    "  requirement: "
                    f"{'PASS' if summary['recent_window_requirement_pass'] else 'FAIL'}"
                ),
            ]
        )
        if summary.get("error"):
            lines.append(f"  error: {summary['error']}")
    lines.extend(
        [
            "",
            f"Decision implication: {report['decision_implication']}",
            "",
            "Safety flags:",
        ]
    )
    flags = report["flags"]
    assert isinstance(flags, dict)
    for key in sorted(flags):
        lines.append(f"- {key}: {str(flags[key]).lower()}")
    return "\n".join(lines) + "\n"


def decision_implication(result: str) -> str:
    if result == RESULT_PASS:
        return "A later DR1 rerun design lock may be considered."
    if result == RESULT_FAIL:
        return (
            "Do not rerun DR1; return to owner decision on alternative "
            "window/source or park freshness reopening."
        )
    if result == RESULT_BLOCKED:
        return "Clarify the blocker; do not improvise with a new source/window."
    raise ValueError(f"unknown acquisition result: {result!r}")


def safety_flags() -> dict[str, bool]:
    return {
        "approved_public_binance_source_only": True,
        "no_private_api": True,
        "no_auth_keys": True,
        "no_dr1_rerun": True,
        "no_gate_change": True,
        "no_filter_introduced": True,
        "no_readiness_promotion": True,
        "research_only": True,
    }


def output_csv_name(symbol: str) -> str:
    validate_symbol_scope(symbol)
    return f"{symbol}_USDT-FUTURES_4H_recent.csv"


def to_epoch_ms(timestamp: datetime) -> int:
    return int(normalize_utc(timestamp).timestamp() * 1000)


def subtract_months(timestamp: datetime, months: int) -> datetime:
    normalized = normalize_utc(timestamp)
    month_index = normalized.month - 1 - months
    year = normalized.year + month_index // 12
    month = month_index % 12 + 1
    day = min(normalized.day, days_in_month(year, month))
    return normalized.replace(year=year, month=month, day=day)


def days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=UTC)
    return (next_month - datetime(year, month, 1, tzinfo=UTC)).days


def format_timedelta(value: timedelta | None) -> str | None:
    if value is None:
        return None
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def decimal_hours(value: timedelta | None) -> str | None:
    if value is None:
        return None
    return str(Decimal(value.total_seconds()) / Decimal("3600"))


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return normalize_utc(value).isoformat()
