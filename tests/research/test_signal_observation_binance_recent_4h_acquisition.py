"""Tests for bounded Binance recent 4H acquisition validation."""

from __future__ import annotations

import ast
import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from research.signal_observation.binance_recent_4h_downloader import (
    EXPECTED_STEP,
    RESULT_BLOCKED,
    RESULT_FAIL,
    RESULT_PASS,
    SYMBOLS,
    LockedWindow,
    build_validation_report,
    classify_acquisition_result,
    create_locked_window,
    output_csv_name,
    run_binance_recent_4h_acquisition,
    safety_flags,
    validate_symbol_csv,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _locked_window() -> LockedWindow:
    return LockedWindow(
        acquisition_task_started_utc=datetime(2026, 5, 12, 11, 17, tzinfo=UTC),
        locked_window_start_utc=datetime(2025, 11, 12, 8, tzinfo=UTC),
        locked_window_end_utc=datetime(2026, 5, 12, 8, tzinfo=UTC),
    )


def _write_csv(path: Path, timestamps: list[datetime]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("timestamp", "open", "high", "low", "close", "volume"))
        for index, timestamp in enumerate(timestamps):
            price = 100 + index
            writer.writerow(
                (
                    timestamp.isoformat().replace("+00:00", "Z"),
                    str(price),
                    str(price + 1),
                    str(price - 1),
                    str(price),
                    "10",
                )
            )


def _timestamps(window: LockedWindow) -> list[datetime]:
    output = []
    current = window.locked_window_start_utc
    while current <= window.locked_window_end_utc:
        output.append(current)
        current += EXPECTED_STEP
    return output


def _passing_summary(symbol: str = "BTCUSDT") -> dict[str, object]:
    return {
        "symbol": symbol,
        "recent_window_requirement_pass": True,
    }


def test_locked_window_is_not_mutated_after_initialization(tmp_path: Path) -> None:
    locked = _locked_window()
    windows_seen: list[LockedWindow] = []

    def fake_fetcher(symbol: str, window: LockedWindow, output_csv: Path) -> Path:
        windows_seen.append(window)
        _write_csv(output_csv, _timestamps(window))
        return output_csv

    report = run_binance_recent_4h_acquisition(
        locked_window=locked,
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "output",
        fetcher=fake_fetcher,
    )

    assert report["locked_window"] == locked.as_report()
    assert windows_seen == [locked, locked, locked]


def test_create_locked_window_uses_latest_completed_4h_boundary() -> None:
    locked = create_locked_window(datetime(2026, 5, 12, 11, 59, tzinfo=UTC))

    assert locked.locked_window_end_utc == datetime(2026, 5, 12, 4, tzinfo=UTC)
    assert locked.locked_window_start_utc == datetime(2025, 11, 12, 4, tzinfo=UTC)


def test_classifies_pass_fail_and_blocked_results() -> None:
    assert (
        classify_acquisition_result([_passing_summary(symbol) for symbol in SYMBOLS], blocked=False)
        == RESULT_PASS
    )
    assert (
        classify_acquisition_result(
            [
                _passing_summary("BTCUSDT"),
                {"symbol": "ETHUSDT", "recent_window_requirement_pass": False},
                _passing_summary("SOLUSDT"),
            ],
            blocked=False,
        )
        == RESULT_FAIL
    )
    assert classify_acquisition_result([], blocked=True) == RESULT_BLOCKED


def test_max_gap_and_contiguity_validation_pass(tmp_path: Path) -> None:
    locked = _locked_window()
    csv_path = tmp_path / output_csv_name("BTCUSDT")
    _write_csv(csv_path, _timestamps(locked))

    summary = validate_symbol_csv(csv_path, "BTCUSDT", locked)

    assert summary["row_count"] == len(_timestamps(locked))
    assert summary["max_gap_hours"] == "4"
    assert summary["gap_count_above_expected_4h_step"] == 0
    assert summary["contiguity_pass"] is True
    assert summary["recent_window_requirement_pass"] is True


def test_gap_above_expected_step_fails_contiguity(tmp_path: Path) -> None:
    locked = _locked_window()
    timestamps = _timestamps(locked)
    timestamps.pop(3)
    csv_path = tmp_path / output_csv_name("BTCUSDT")
    _write_csv(csv_path, timestamps)

    summary = validate_symbol_csv(csv_path, "BTCUSDT", locked)

    assert summary["max_gap_hours"] == "8"
    assert summary["gap_count_above_expected_4h_step"] == 1
    assert summary["contiguity_pass"] is False
    assert summary["recent_window_requirement_pass"] is False


def test_duplicate_timestamp_detection(tmp_path: Path) -> None:
    locked = _locked_window()
    timestamps = _timestamps(locked)
    timestamps.insert(2, timestamps[2])
    csv_path = tmp_path / output_csv_name("BTCUSDT")
    _write_csv(csv_path, timestamps)

    summary = validate_symbol_csv(csv_path, "BTCUSDT", locked)

    assert summary["duplicate_timestamp_count"] == 1
    assert summary["timestamps_monotonic"] is False
    assert summary["contiguity_pass"] is False


def test_monotonic_timestamp_validation(tmp_path: Path) -> None:
    locked = _locked_window()
    timestamps = _timestamps(locked)
    timestamps[1], timestamps[2] = timestamps[2], timestamps[1]
    csv_path = tmp_path / output_csv_name("BTCUSDT")
    _write_csv(csv_path, timestamps)

    summary = validate_symbol_csv(csv_path, "BTCUSDT", locked)

    assert summary["timestamps_monotonic"] is False
    assert summary["recent_window_requirement_pass"] is False


def test_requirement_pass_requires_all_three_symbols(tmp_path: Path) -> None:
    locked = _locked_window()

    def fake_fetcher(symbol: str, window: LockedWindow, output_csv: Path) -> Path:
        timestamps = _timestamps(window)
        if symbol == "SOLUSDT":
            timestamps.pop(4)
        _write_csv(output_csv, timestamps)
        return output_csv

    report = run_binance_recent_4h_acquisition(
        locked_window=locked,
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "output",
        fetcher=fake_fetcher,
    )

    assert report["result"] == RESULT_FAIL
    assert report["per_symbol"]["SOLUSDT"]["recent_window_requirement_pass"] is False


def test_blocked_when_approved_source_path_cannot_complete(tmp_path: Path) -> None:
    locked = _locked_window()

    def blocked_fetcher(symbol: str, window: LockedWindow, output_csv: Path) -> Path:
        raise ValueError(f"{symbol} unavailable")

    report = run_binance_recent_4h_acquisition(
        locked_window=locked,
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "output",
        fetcher=blocked_fetcher,
    )

    assert report["result"] == RESULT_BLOCKED
    assert report["errors"]


def test_public_source_scope_guard_and_safety_flags() -> None:
    flags = safety_flags()

    assert flags["approved_public_binance_source_only"] is True
    assert flags["no_private_api"] is True
    assert flags["no_auth_keys"] is True
    assert flags["no_dr1_rerun"] is True
    assert flags["no_readiness_promotion"] is True


def test_report_generation_does_not_overclaim_readiness() -> None:
    locked = _locked_window()
    report = build_validation_report(
        locked_window=locked,
        result=RESULT_PASS,
        per_symbol={symbol: _passing_summary(symbol) for symbol in SYMBOLS},
        csv_paths={symbol: f"{symbol}.csv" for symbol in SYMBOLS},
        errors={},
    )

    assert report["flags"]["no_readiness_promotion"] is True
    assert report["flags"]["no_gate_change"] is True
    assert "DR1 rerun design lock may be considered" in report["decision_implication"]


def test_no_private_endpoint_or_auth_tokens_static_guard() -> None:
    module_path = (
        REPO_ROOT
        / "research"
        / "signal_observation"
        / "binance_recent_4h_downloader.py"
    )
    text = module_path.read_text(encoding="utf-8")
    forbidden_tokens = (
        "X-MBX-APIKEY",
        "/fapi/v1/account",
        "/fapi/v1/order",
        "/fapi/v2/account",
        "/fapi/v2/positionRisk",
        "/fapi/v1/listenKey",
        "openOrders",
        "myTrades",
        "set_leverage",
        "withdraw",
        "transfer",
    )

    for token in forbidden_tokens:
        assert token not in text


def test_no_unapproved_network_library_imports() -> None:
    module_path = (
        REPO_ROOT
        / "research"
        / "signal_observation"
        / "binance_recent_4h_downloader.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert "requests" not in imported_modules
    assert "httpx" not in imported_modules
