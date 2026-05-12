"""Tests for bounded DR1 Binance recent rerun."""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research.signal_observation.candles import Candle
from research.signal_observation.setup_c_dr1_binance_recent_rerun import (
    ANALYSIS_INCONCLUSIVE,
    ANALYSIS_SUPPORTIVE,
    ANALYSIS_WEAK,
    OUTCOME_HIGH,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_LOW,
    RERUN_WINDOW_END,
    RERUN_WINDOW_START,
    SYMBOLS,
    analyze_dr1_binance_recent_rerun,
    classify_dr1_outcome,
    classify_lead_lag,
    decision_implication,
    evaluate_binance_recent_freshness,
    rerun_input_window,
    safety_flags,
    _validate_symbol_scope,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _candles(
    start: datetime = RERUN_WINDOW_START,
    count: int = 1087,
    *,
    base: Decimal = Decimal("100"),
    step: Decimal = Decimal("1"),
) -> list[Candle]:
    candles = []
    for index in range(count):
        close = base + (step * Decimal(index))
        candles.append(
            Candle(
                timestamp=start + timedelta(hours=4 * index),
                open=close,
                high=close + Decimal("1"),
                low=close - Decimal("1"),
                close=close,
                volume=Decimal("10"),
            )
        )
    return candles


def _all_symbols(candles: list[Candle]) -> dict[str, list[Candle]]:
    return {symbol: list(candles) for symbol in SYMBOLS}


def test_committed_rerun_window_metadata_is_preserved() -> None:
    window = rerun_input_window()

    assert window["start_utc"] == "2025-11-12T12:00:00+00:00"
    assert window["end_utc"] == "2026-05-12T12:00:00+00:00"
    assert window["symbols"] == list(SYMBOLS)
    assert window["expected_rows_per_symbol"] == 1087


def test_freshness_eligible_path() -> None:
    result = evaluate_binance_recent_freshness(_all_symbols(_candles()))

    assert result["eligible"] is True
    assert result["per_symbol"]["BTCUSDT"]["latest_candle"] == RERUN_WINDOW_END.isoformat()


def test_validate_symbol_scope_rejects_invalid_symbol_set() -> None:
    with pytest.raises(ValueError, match="symbols must be exactly"):
        _validate_symbol_scope({"BTCUSDT": _candles()})


def test_outcome_classification_high_low_and_inconclusive() -> None:
    supportive = {
        "a": {"outcome": ANALYSIS_SUPPORTIVE},
        "b": {"outcome": ANALYSIS_SUPPORTIVE},
    }
    weak = {
        "a": {"outcome": ANALYSIS_SUPPORTIVE},
        "b": {"outcome": ANALYSIS_WEAK},
    }
    mixed = {
        "a": {"outcome": ANALYSIS_SUPPORTIVE},
        "b": {"outcome": ANALYSIS_INCONCLUSIVE},
    }

    assert classify_dr1_outcome(freshness_eligible=True, analyses=supportive) == OUTCOME_HIGH
    assert classify_dr1_outcome(freshness_eligible=True, analyses=weak) == OUTCOME_LOW
    assert (
        classify_dr1_outcome(freshness_eligible=True, analyses=mixed)
        == OUTCOME_INCONCLUSIVE
    )
    assert (
        classify_dr1_outcome(freshness_eligible=False, analyses=supportive)
        == OUTCOME_INCONCLUSIVE
    )


def test_low_branch_when_freshness_eligible_but_analysis_is_weak() -> None:
    analyses = {
        "non_overlapping_return_autocorrelation": {"outcome": ANALYSIS_SUPPORTIVE},
        "variance_ratio_predictability": {"outcome": ANALYSIS_WEAK},
        "btc_to_eth_sol_lead_lag": {"outcome": ANALYSIS_INCONCLUSIVE},
        "setup_c_recent_out_of_window_persistence": {"outcome": ANALYSIS_SUPPORTIVE},
    }

    assert classify_dr1_outcome(freshness_eligible=True, analyses=analyses) == OUTCOME_LOW


def test_lead_lag_supportive_rule_is_reused() -> None:
    assert classify_lead_lag(Decimal("0.61"), 20) == ANALYSIS_SUPPORTIVE
    assert classify_lead_lag(Decimal("0.60"), 20) == ANALYSIS_INCONCLUSIVE
    assert classify_lead_lag(Decimal("0.80"), 19) == ANALYSIS_INCONCLUSIVE


def test_decision_implication_mapping() -> None:
    assert "may be considered" in decision_implication(OUTCOME_HIGH)
    assert "Do not open" in decision_implication(OUTCOME_LOW)
    assert "remaining blocker" in decision_implication(OUTCOME_INCONCLUSIVE)


def test_report_safety_flags_and_no_readiness_overclaim() -> None:
    flags = safety_flags()

    assert flags == {
        "committed_binance_recent_data_only": True,
        "no_new_downloads": True,
        "no_network_calls": True,
        "no_threshold_change": True,
        "no_dr1_scope_expansion": True,
        "no_readiness_promotion": True,
        "research_only": True,
    }


def test_report_contains_safety_flags() -> None:
    report = analyze_dr1_binance_recent_rerun(_all_symbols(_candles()))

    assert report["flags"]["committed_binance_recent_data_only"] is True
    assert report["flags"]["no_readiness_promotion"] is True
    assert report["rerun_input_window"]["start_utc"] == RERUN_WINDOW_START.isoformat()


def test_no_network_imports_or_download_path() -> None:
    module_path = (
        REPO_ROOT
        / "research"
        / "signal_observation"
        / "setup_c_dr1_binance_recent_rerun.py"
    )
    text = module_path.read_text(encoding="utf-8")
    forbidden_tokens = (
        "url" + "lib",
        "requests",
        "httpx",
        "download_binance",
        "fapi.binance.com",
        "X-MBX-APIKEY",
    )
    for token in forbidden_tokens:
        assert token not in text

    tree = ast.parse(text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert "requests" not in imported_modules
    assert "urllib.request" not in imported_modules
