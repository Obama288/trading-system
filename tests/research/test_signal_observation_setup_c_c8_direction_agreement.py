"""Tests for Stage 54-SQ C8 direction-call agreement diagnostic."""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from research.signal_observation.setup_c_c8_direction_agreement import (
    DirectionCall,
    classify_interpretation,
    evaluate_direction_agreement,
    normalize_timestamp_iso,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _calls(
    venue: str,
    symbol: str,
    directions: list[int],
    *,
    start: datetime = datetime(2024, 1, 1, tzinfo=UTC),
) -> list[DirectionCall]:
    return [
        DirectionCall(
            venue=venue,
            symbol=symbol,
            timestamp=(start + timedelta(hours=4 * index)).isoformat(),
            window="development",
            lookback=40,
            direction=direction,
        )
        for index, direction in enumerate(directions)
    ]


def test_timestamp_normalization_to_utc_iso_8601() -> None:
    timestamp = datetime(2024, 1, 1, 3, tzinfo=timezone(timedelta(hours=3)))

    assert normalize_timestamp_iso(timestamp) == "2024-01-01T00:00:00+00:00"
    assert normalize_timestamp_iso("2024-01-01T00:00:00Z") == "2024-01-01T00:00:00+00:00"


def test_alignment_key_is_symbol_plus_timestamp() -> None:
    ts = "2024-01-01T00:00:00+00:00"
    bitget = [
        DirectionCall("bitget", "BTCUSDT", ts, "development", 40, 1),
        DirectionCall("bitget", "ETHUSDT", ts, "development", 40, -1),
    ]
    binance = [
        DirectionCall("binance", "BTCUSDT", ts, "development", 40, 1),
        DirectionCall("binance", "ETHUSDT", ts, "development", 40, 1),
    ]

    result = evaluate_direction_agreement(bitget, binance, window="development")

    assert result["symbols"]["BTCUSDT"]["matching_direction_count"] == 1
    assert result["symbols"]["ETHUSDT"]["opposite_direction_count"] == 1


def test_missing_rows_excluded_from_agreement_numerator_and_denominator() -> None:
    bitget = _calls("bitget", "BTCUSDT", [1, 1, -1])
    binance = _calls("binance", "BTCUSDT", [1])

    result = evaluate_direction_agreement(bitget, binance, window="development")
    btc = result["symbols"]["BTCUSDT"]

    assert btc["aligned_row_count"] == 1
    assert btc["matching_direction_count"] == 1
    assert btc["opposite_direction_count"] == 0
    assert btc["bitget_only_missing_count"] == 2
    assert btc["binance_only_missing_count"] == 0
    assert btc["total_coverage_denominator"] == 3
    assert btc["agreement_pct"] == "100"


def test_minimum_aligned_rows_below_50_is_mixed_or_inconclusive() -> None:
    label = classify_interpretation(
        agreement=Decimal("1"),
        missing_coverage=Decimal("0"),
        aligned_row_count=49,
    )

    assert label == "mixed_or_inconclusive"


def test_missing_coverage_above_10pct_is_mixed_or_inconclusive() -> None:
    label = classify_interpretation(
        agreement=Decimal("1"),
        missing_coverage=Decimal("0.11"),
        aligned_row_count=50,
    )

    assert label == "mixed_or_inconclusive"


def test_high_agreement_gte_80pct_classification() -> None:
    bitget = _calls("bitget", "BTCUSDT", [1] * 80 + [-1] * 20)
    binance = _calls("binance", "BTCUSDT", [1] * 100)

    result = evaluate_direction_agreement(bitget, binance, window="development")

    assert result["symbols"]["BTCUSDT"]["agreement_pct"] == "80.0"
    assert (
        result["symbols"]["BTCUSDT"]["interpretation_label"]
        == "high_direction_agreement_magnitude_divergence"
    )


def test_low_agreement_lt_60pct_classification() -> None:
    bitget = _calls("bitget", "BTCUSDT", [1] * 59 + [-1] * 41)
    binance = _calls("binance", "BTCUSDT", [1] * 100)

    result = evaluate_direction_agreement(bitget, binance, window="development")

    assert result["symbols"]["BTCUSDT"]["agreement_pct"] == "59.00"
    assert (
        result["symbols"]["BTCUSDT"]["interpretation_label"]
        == "low_direction_agreement_signal_divergence"
    )


def test_safety_flags_are_read_only_and_no_readiness() -> None:
    from research.signal_observation.setup_c_c8_direction_agreement import _safety_flags

    assert _safety_flags() == {
        "observational_only": True,
        "c7_verdicts_read_only": True,
        "no_gate_change": True,
        "no_filter_introduced": True,
        "no_readiness_promotion": True,
        "no_new_downloads": True,
    }


def test_no_network_static_import_guard() -> None:
    module_path = (
        REPO_ROOT
        / "research"
        / "signal_observation"
        / "setup_c_c8_direction_agreement.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    forbidden = {
        "url" + "lib",
        "url" + "lib.request",
        "url" + "lib.parse",
        "requ" + "ests",
        "http" + ".client",
        "http" + "x",
        "sock" + "et",
    }
    assert not forbidden.intersection(imported_modules)
