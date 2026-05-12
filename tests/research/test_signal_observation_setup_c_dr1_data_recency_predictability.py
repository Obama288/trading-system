"""Tests for Stage 54-SQ DR1 data recency / predictability reconnaissance."""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from research.signal_observation.candles import Candle
from research.signal_observation.setup_c_dr1_data_recency_predictability import (
    ANALYSIS_INCONCLUSIVE,
    ANALYSIS_SUPPORTIVE,
    ANALYSIS_WEAK,
    OUTCOME_HIGH,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_LOW,
    _decision_implication,
    analyze_dr1_data_recency_predictability,
    classify_dr1_outcome,
    classify_lead_lag,
    evaluate_freshness,
    safety_flags,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
IMPLEMENTATION_DATE = datetime(2026, 5, 12, tzinfo=UTC)


def _candles(
    start: datetime,
    count: int,
    *,
    base: Decimal = Decimal("100"),
    step: Decimal = Decimal("1"),
) -> list[Candle]:
    output = []
    for index in range(count):
        close = base + (step * Decimal(index))
        output.append(
            Candle(
                timestamp=start + timedelta(hours=4 * index),
                open=close,
                high=close + Decimal("1"),
                low=close - Decimal("1"),
                close=close,
                volume=Decimal("10"),
            )
        )
    return output


def _all_series(candles: list[Candle]) -> dict[str, dict[str, list[Candle]]]:
    return {
        venue: {symbol: list(candles) for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}
        for venue in ("bitget", "binance")
    }


def test_freshness_requirement_satisfied() -> None:
    candles = _candles(datetime(2025, 10, 1, tzinfo=UTC), 1200)

    result = evaluate_freshness(
        _all_series(candles),
        implementation_date=IMPLEMENTATION_DATE,
    )

    assert result["eligible"] is True


def test_freshness_requirement_not_satisfied_when_latest_is_stale() -> None:
    candles = _candles(datetime(2025, 1, 1, tzinfo=UTC), 800)

    result = evaluate_freshness(
        _all_series(candles),
        implementation_date=IMPLEMENTATION_DATE,
    )

    assert result["eligible"] is False


def test_inconclusive_when_freshness_data_is_unavailable() -> None:
    candles = _candles(datetime(2025, 1, 1, tzinfo=UTC), 20)

    report = analyze_dr1_data_recency_predictability(
        _all_series(candles),
        implementation_date=IMPLEMENTATION_DATE,
    )

    assert report["dr1_decision"] == OUTCOME_INCONCLUSIVE
    assert report["missing_data_requirement"] is not None


def test_lead_lag_above_60pct_is_supportive() -> None:
    assert classify_lead_lag(Decimal("0.61"), 20) == ANALYSIS_SUPPORTIVE


def test_lead_lag_at_or_below_60pct_or_underpowered_is_inconclusive() -> None:
    assert classify_lead_lag(Decimal("0.60"), 20) == ANALYSIS_INCONCLUSIVE
    assert classify_lead_lag(Decimal("0.90"), 19) == ANALYSIS_INCONCLUSIVE


def test_deterministic_outcome_classification() -> None:
    analyses = {
        "a": {"outcome": ANALYSIS_SUPPORTIVE},
        "b": {"outcome": ANALYSIS_SUPPORTIVE},
        "c": {"outcome": ANALYSIS_SUPPORTIVE},
    }

    assert classify_dr1_outcome(freshness_eligible=True, analyses=analyses) == OUTCOME_HIGH
    assert (
        classify_dr1_outcome(freshness_eligible=False, analyses=analyses)
        == OUTCOME_INCONCLUSIVE
    )


def test_deterministic_outcome_classification_low_branch() -> None:
    analyses = {
        "a": {"outcome": ANALYSIS_SUPPORTIVE},
        "b": {"outcome": ANALYSIS_WEAK},
        "c": {"outcome": ANALYSIS_INCONCLUSIVE},
    }

    assert classify_dr1_outcome(freshness_eligible=True, analyses=analyses) == OUTCOME_LOW
    assert "Park Setup C" in _decision_implication(OUTCOME_LOW)


def test_safety_flags_do_not_overclaim_readiness_or_gate_change() -> None:
    assert safety_flags() == {
        "no_new_downloads": True,
        "observational_only": True,
        "no_readiness_promotion": True,
        "no_gate_change": True,
        "no_filter_introduced": True,
        "research_only": True,
    }


def test_no_network_static_import_guard() -> None:
    module_path = (
        REPO_ROOT
        / "research"
        / "signal_observation"
        / "setup_c_dr1_data_recency_predictability.py"
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


def test_report_safety_flags_and_no_readiness_gate_overclaim() -> None:
    candles = _candles(datetime(2025, 1, 1, tzinfo=UTC), 20)

    report = analyze_dr1_data_recency_predictability(
        _all_series(candles),
        implementation_date=IMPLEMENTATION_DATE,
    )

    assert report["flags"]["no_readiness_promotion"] is True
    assert report["flags"]["no_gate_change"] is True
    assert report["flags"]["observational_only"] is True
    assert "paper-candidate design lock" in report["decision_implication"]
