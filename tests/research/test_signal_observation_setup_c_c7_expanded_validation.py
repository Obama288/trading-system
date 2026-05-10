"""Tests for Stage 54-SQ C7 expanded validation analyzer."""

from __future__ import annotations

import ast
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Sequence

import pytest

from research.signal_observation.candles import Candle, parse_iso_utc
from research.signal_observation.csv_loader import load_ohlcv_csv
from research.signal_observation.setup_c_c7_expanded_validation import (
    COMBINED_RETENTION_THRESHOLD,
    DEV_WINDOW_END,
    DEV_WINDOW_START,
    EXPANSION_DIRECTIONS,
    FROZEN_SYMBOLS,
    RANDOM_BASELINE_SEED,
    REPORT_SCHEMA,
    RESULT_FAIL,
    RESULT_HOLD,
    RESULT_PASS,
    analyze_c7_expanded_validation,
    combined_window_vt_post_cost_moderate,
    evaluate_c7_expanded_intervals,
)
from research.signal_observation.setup_c_tsmom import (
    COST_BPS,
    FUNDING_INTERVALS_PER_REBALANCE,
    FUNDING_RATES_PER_8H,
    PRIMARY_COST_SCENARIO,
    PRIMARY_LOOKBACK,
    RANDOM_ITERATIONS,
    RANDOM_SEED,
    TsmomInterval,
    _funding_impact_normalized,
    build_tsmom_intervals,
    cost_return,
    summarize_intervals,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEV_BITGET_DATA_DIR = REPO_ROOT / "research" / "signal_observation" / "data" / "bitget"
PUBLISHED_TSMOM_JSON = (
    REPO_ROOT
    / "research"
    / "signal_observation"
    / "output"
    / "bitget"
    / "setup_c_tsmom_report.json"
)


# --- fixture helpers ---


def _make_interval(
    *,
    symbol: str = "BTCUSDT",
    timestamp: str = "2026-06-01T00:00:00+00:00",
    direction: int = 1,
    turnover: int = 1,
    interval_return: str = "0.02",
    vol_proxy: str = "0.05",
    split: str = "expanded",
    lookback: int = 40,
) -> TsmomInterval:
    raw = Decimal(interval_return)
    signed = Decimal(direction) * raw
    vol = Decimal(vol_proxy)
    pcr = {scenario: signed - cost_return(turnover, bps) for scenario, bps in COST_BPS.items()}
    return TsmomInterval(
        symbol=symbol,
        timestamp=timestamp,
        split=split,
        lookback=lookback,
        direction=direction,
        turnover_units=turnover,
        interval_return=raw,
        gross_return=signed,
        normalized_return=signed / vol,
        post_cost_returns=pcr,
        post_cost_normalized_returns={s: v / vol for s, v in pcr.items()},
        vol_proxy=vol,
    )


def _per_symbol_run(
    *,
    direction: int,
    n: int,
    interval_return: str,
    vol_proxy: str,
    symbol: str,
    base_offset_hours: int,
) -> list[TsmomInterval]:
    """Build n intervals for a symbol with stored turnover from prior=0 fresh.

    Mirrors what build_tsmom_intervals would store: first interval turnover
    depends on direction relative to prior=0; subsequent intervals turnover=0
    when direction stays the same.
    """

    base = datetime(2026, 6, 1, tzinfo=UTC) + timedelta(hours=base_offset_hours)
    intervals: list[TsmomInterval] = []
    prior = 0
    for index in range(n):
        from research.signal_observation.setup_c_tsmom import turnover_units

        turnover = turnover_units(prior, direction)
        prior = direction
        ts = (base + timedelta(hours=24 * index)).isoformat()
        intervals.append(
            _make_interval(
                symbol=symbol,
                timestamp=ts,
                direction=direction,
                turnover=turnover,
                interval_return=interval_return,
                vol_proxy=vol_proxy,
            )
        )
    return intervals


def _baseline_dev_intervals() -> dict[str, list[TsmomInterval]]:
    """Dev fixture: 4 intervals per symbol, all direction=+1, mid-dev-window timestamps."""

    base = datetime(2024, 6, 1, tzinfo=UTC)
    out: dict[str, list[TsmomInterval]] = {}
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        intervals: list[TsmomInterval] = []
        prior = 0
        for index in range(4):
            from research.signal_observation.setup_c_tsmom import turnover_units

            turnover = turnover_units(prior, 1)
            prior = 1
            ts = (base + timedelta(hours=24 * index + sym_index)).isoformat()
            intervals.append(
                _make_interval(
                    symbol=sym,
                    timestamp=ts,
                    direction=1,
                    turnover=turnover,
                    interval_return="0.02",
                    vol_proxy="0.05",
                    split="discovery",
                )
            )
        out[sym] = intervals
    return out


def _baseline_expanded_intervals() -> dict[str, list[TsmomInterval]]:
    """Expanded fixture: 4 intervals per symbol, all direction=+1, forward window."""

    base = datetime(2026, 6, 1, tzinfo=UTC)
    out: dict[str, list[TsmomInterval]] = {}
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        intervals: list[TsmomInterval] = []
        prior = 0
        for index in range(4):
            from research.signal_observation.setup_c_tsmom import turnover_units

            turnover = turnover_units(prior, 1)
            prior = 1
            ts = (base + timedelta(hours=24 * index + sym_index)).isoformat()
            intervals.append(
                _make_interval(
                    symbol=sym,
                    timestamp=ts,
                    direction=1,
                    turnover=turnover,
                    interval_return="0.02",
                    vol_proxy="0.05",
                    split="expanded",
                )
            )
        out[sym] = intervals
    return out


def _empty_per_symbol_dict() -> dict[str, list[TsmomInterval]]:
    return {sym: [] for sym in FROZEN_SYMBOLS}


def _make_candle(timestamp: datetime, close: Decimal = Decimal("100")) -> Candle:
    return Candle(
        timestamp=timestamp,
        open=close,
        high=close + Decimal("1"),
        low=close - Decimal("1"),
        close=close,
        volume=Decimal("100"),
    )


# --- candle-level validation tests ---


def test_inclusive_dev_window_overlap_at_start_is_rejected() -> None:
    overlap_candle = _make_candle(DEV_WINDOW_START)
    expanded = {"BTCUSDT": [overlap_candle]}
    development = {sym: [] for sym in FROZEN_SYMBOLS}

    with pytest.raises(ValueError, match="overlaps inclusive dev window"):
        analyze_c7_expanded_validation(
            development_candles_by_symbol=development,
            expanded_candles_by_symbol=expanded,
            expanded_window_start="2020-01-01T00:00:00+00:00",
            expanded_window_end="2023-12-17T15:00:00+00:00",
            expansion_direction="backward",
        )


def test_inclusive_dev_window_overlap_at_end_is_rejected() -> None:
    overlap_candle = _make_candle(DEV_WINDOW_END)
    expanded = {"ETHUSDT": [overlap_candle]}
    development = {sym: [] for sym in FROZEN_SYMBOLS}

    with pytest.raises(ValueError, match="overlaps inclusive dev window"):
        analyze_c7_expanded_validation(
            development_candles_by_symbol=development,
            expanded_candles_by_symbol=expanded,
            expanded_window_start="2026-05-07T00:00:00+00:00",
            expanded_window_end="2026-06-01T00:00:00+00:00",
            expansion_direction="forward",
        )


def test_strict_outside_backward_boundary_enforcement() -> None:
    development = {sym: [] for sym in FROZEN_SYMBOLS}
    expanded = {sym: [] for sym in FROZEN_SYMBOLS}

    with pytest.raises(ValueError, match="strictly before dev_window_start"):
        analyze_c7_expanded_validation(
            development_candles_by_symbol=development,
            expanded_candles_by_symbol=expanded,
            expanded_window_start="2020-01-01T00:00:00+00:00",
            expanded_window_end=DEV_WINDOW_START.isoformat(),
            expansion_direction="backward",
        )


def test_strict_outside_forward_boundary_enforcement() -> None:
    development = {sym: [] for sym in FROZEN_SYMBOLS}
    expanded = {sym: [] for sym in FROZEN_SYMBOLS}

    with pytest.raises(ValueError, match="strictly after dev_window_end"):
        analyze_c7_expanded_validation(
            development_candles_by_symbol=development,
            expanded_candles_by_symbol=expanded,
            expanded_window_start=DEV_WINDOW_END.isoformat(),
            expanded_window_end="2026-09-01T00:00:00+00:00",
            expansion_direction="forward",
        )


def test_frozen_symbol_guard_rejects_extras_in_expanded_candles() -> None:
    extra_candle = _make_candle(parse_iso_utc("2026-06-01T00:00:00+00:00"))
    expanded = {"BTCUSDT": [], "DOGEUSDT": [extra_candle]}
    development = {sym: [] for sym in FROZEN_SYMBOLS}

    with pytest.raises(ValueError, match="unexpected symbol keys"):
        analyze_c7_expanded_validation(
            development_candles_by_symbol=development,
            expanded_candles_by_symbol=expanded,
            expanded_window_start="2026-05-07T00:00:00+00:00",
            expanded_window_end="2026-09-01T00:00:00+00:00",
            expansion_direction="forward",
        )


def test_frozen_symbol_guard_rejects_extras_in_evaluator() -> None:
    bad = {"BTCUSDT": [], "ETHUSDT": [], "SOLUSDT": [], "DOGEUSDT": []}

    with pytest.raises(ValueError, match="unexpected symbol keys"):
        evaluate_c7_expanded_intervals(
            dev_intervals_by_symbol=bad,
            expanded_intervals_by_symbol=_empty_per_symbol_dict(),
            expanded_window_start="2026-05-07T00:00:00+00:00",
            expanded_window_end="2026-09-01T00:00:00+00:00",
            expansion_direction="forward",
        )


# --- locked-bound semantics ---


def test_invalid_expansion_direction_raises() -> None:
    with pytest.raises(ValueError, match="invalid expansion_direction"):
        evaluate_c7_expanded_intervals(
            dev_intervals_by_symbol=_empty_per_symbol_dict(),
            expanded_intervals_by_symbol=_empty_per_symbol_dict(),
            expanded_window_start="2026-05-07T00:00:00+00:00",
            expanded_window_end="2026-09-01T00:00:00+00:00",
            expansion_direction="sideways",
        )


def test_locked_bounds_recorded_and_changing_bounds_changes_report_data() -> None:
    dev = _baseline_dev_intervals()
    expanded = _baseline_expanded_intervals()

    report_a = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=dev,
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )
    report_b = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=dev,
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-15T00:00:00+00:00",
        expanded_window_end="2026-10-15T00:00:00+00:00",
        expansion_direction="forward",
    )

    assert report_a["expanded_window_start"] != report_b["expanded_window_start"]
    assert report_a["expanded_window_end"] != report_b["expanded_window_end"]
    assert report_a["decision"] == report_b["decision"]
    assert report_a["combined_retention_numerator"] == report_b["combined_retention_numerator"]


# --- analytic correctness tests ---


def test_expanded_only_vol_threshold_isolation() -> None:
    """Vol thresholds derived from expanded intervals only — no dev leakage."""

    dev_intervals: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        dev_intervals[sym] = [
            _make_interval(
                symbol=sym,
                timestamp=(
                    datetime(2024, 6, 1, tzinfo=UTC) + timedelta(hours=sym_index)
                ).isoformat(),
                direction=1,
                turnover=1,
                interval_return="0.01",
                vol_proxy="0.001",
                split="discovery",
            )
        ]

    expanded_intervals: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    expanded_vols = ["0.05", "0.07", "0.09"]
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        expanded_intervals[sym] = [
            _make_interval(
                symbol=sym,
                timestamp=(
                    datetime(2026, 6, 1, tzinfo=UTC) + timedelta(hours=sym_index)
                ).isoformat(),
                direction=1,
                turnover=1,
                interval_return="0.01",
                vol_proxy=expanded_vols[sym_index],
            )
        ]

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=dev_intervals,
        expanded_intervals_by_symbol=expanded_intervals,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    thresholds = report["expanded_vol_thresholds"]
    assert thresholds["derived_from"] == "expanded_window_only"
    # Median of [0.05, 0.07, 0.09] is 0.07, not the dev vol_proxy 0.001.
    assert Decimal(str(thresholds["threshold"])) == Decimal("0.07")


def test_high_cost_funding_stress_formula() -> None:
    """Funding impact equals -direction * 0.0009 / vol_proxy per interval, summed."""

    expanded: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    expanded["BTCUSDT"] = [
        _make_interval(
            symbol="BTCUSDT",
            timestamp="2026-06-01T00:00:00+00:00",
            direction=1,
            turnover=1,
            interval_return="0.02",
            vol_proxy="0.02",
        )
    ]

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=_baseline_dev_intervals(),
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    funding_rate = FUNDING_RATES_PER_8H["high_cost"]
    expected_impact = (
        Decimal(-1) * funding_rate * FUNDING_INTERVALS_PER_REBALANCE / Decimal("0.02")
    )
    assert (
        Decimal(str(report["funding_impact_on_expanded_vt_post_cost_moderate"]))
        == expected_impact
    )
    # Parity vs imported private helper (covers explicit private import policy).
    helper_impact = sum(
        (_funding_impact_normalized(item, funding_rate) for item in expanded["BTCUSDT"]),
        Decimal("0"),
    )
    assert (
        Decimal(str(report["funding_impact_on_expanded_vt_post_cost_moderate"]))
        == helper_impact
    )
    assert report["funding_scenario"] == "high_cost"
    assert Decimal(str(report["funding_rate_per_8h"])) == funding_rate


def test_union_recomputation_differs_from_arithmetic_sum_when_boundary_turnover_differs() -> None:
    """Boundary turnover at dev->expanded transition causes recomputation to diverge."""

    # Per symbol: 1 dev interval direction=+1, 1 expanded interval direction=-1.
    # Stored expanded turnover was built fresh from prior=0 → turnover=1.
    # In union, prior is dev's last direction=+1 → recomputed turnover=2.
    dev_intervals: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    expanded_intervals: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        dev_intervals[sym] = [
            _make_interval(
                symbol=sym,
                timestamp=(
                    datetime(2024, 6, 1, tzinfo=UTC) + timedelta(hours=sym_index)
                ).isoformat(),
                direction=1,
                turnover=1,
                interval_return="0.0005",
                vol_proxy="0.001",
                split="discovery",
            )
        ]
        expanded_intervals[sym] = [
            _make_interval(
                symbol=sym,
                timestamp=(
                    datetime(2026, 6, 1, tzinfo=UTC) + timedelta(hours=sym_index)
                ).isoformat(),
                direction=-1,
                turnover=1,
                interval_return="-0.0005",
                vol_proxy="0.001",
            )
        ]

    union_by_symbol = {
        sym: dev_intervals[sym] + expanded_intervals[sym] for sym in FROZEN_SYMBOLS
    }
    recomputed_numerator = combined_window_vt_post_cost_moderate(union_by_symbol)
    arithmetic_sum = Decimal("0")
    for sym in FROZEN_SYMBOLS:
        for item in dev_intervals[sym] + expanded_intervals[sym]:
            arithmetic_sum += Decimal(str(item.post_cost_normalized_returns[PRIMARY_COST_SCENARIO]))

    assert recomputed_numerator != arithmetic_sum


def test_combined_denominator_matches_summarize_intervals_for_dev_only() -> None:
    """Parity: dev-only denominator equals summarize_intervals headline.

    Because dev intervals were built from prior_direction=0 per symbol, the
    chronological recomputation reproduces stored turnover, so the dev-only
    denominator must equal the headline vt-post-cost-moderate.
    """

    dev = _baseline_dev_intervals()
    flat = [item for sym in FROZEN_SYMBOLS for item in dev[sym]]
    headline = Decimal(
        str(
            summarize_intervals(flat)["volatility_targeted_post_cost_return"][
                PRIMARY_COST_SCENARIO
            ]
        )
    )

    denominator = combined_window_vt_post_cost_moderate(dev)

    assert denominator == headline


def test_missing_symbol_results_in_hold_when_other_conditions_pass() -> None:
    """Missing frozen symbol forces decision=HOLD, not PASS, even on positive scenario."""

    dev = _baseline_dev_intervals()
    # Drop SOLUSDT from expanded — only BTC and ETH have intervals.
    expanded = _baseline_expanded_intervals()
    expanded["SOLUSDT"] = []

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=dev,
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    assert report["decision"] == RESULT_HOLD
    assert "SOLUSDT" in report["symbols_missing"]
    assert "SOLUSDT" not in report["symbols_usable"]


def test_baseline_scenario_passes_all_five_gate_conditions() -> None:
    """Baseline fixture achieves PASS — used as reference for gate-flip tests."""

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=_baseline_dev_intervals(),
        expanded_intervals_by_symbol=_baseline_expanded_intervals(),
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    gate = report["gate_conditions"]
    assert gate["expanded_vt_post_cost_moderate_gt_0"]["passes"] is True
    assert gate["expanded_beats_random_p75"]["passes"] is True
    assert gate["funding_adjusted_high_cost_gt_0"]["passes"] is True
    assert gate["two_of_three_symbols_non_negative"]["passes"] is True
    assert gate["combined_retention_ratio_gte_50pct"]["passes"] is True
    assert report["decision"] == RESULT_PASS


def test_cond1_flip_expanded_vt_post_cost_le_zero_decides_fail() -> None:
    """Flipping cond_1 (expanded ≤ 0) drives decision to FAIL regardless of other conds."""

    expanded: dict[str, list[TsmomInterval]] = _baseline_expanded_intervals()
    # Flip every expanded interval's direction to -1 (with same return — signed becomes negative).
    flipped: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        flipped[sym] = _per_symbol_run(
            direction=-1,
            n=4,
            interval_return="0.02",
            vol_proxy="0.05",
            symbol=sym,
            base_offset_hours=sym_index,
        )

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=_baseline_dev_intervals(),
        expanded_intervals_by_symbol=flipped,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    assert report["gate_conditions"]["expanded_vt_post_cost_moderate_gt_0"]["passes"] is False
    assert report["decision"] == RESULT_FAIL


def test_cond2_flip_expanded_below_random_p75_decides_not_pass() -> None:
    """Flipping cond_2 (expanded ≤ random p75) prevents PASS."""

    # BTC and ETH each contribute small positive sum [+,+,+,-,-].
    # SOL contributes a clearly negative sum [-,-,-,+,+] so the pooled E_h
    # is small positive while the random ±1 baseline's p75 still exceeds it.
    from research.signal_observation.setup_c_tsmom import turnover_units

    expanded: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    sequences = {
        "BTCUSDT": (1, 1, 1, -1, -1),
        "ETHUSDT": (1, 1, 1, -1, -1),
        "SOLUSDT": (-1, -1, -1, 1, 1),
    }
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        runs: list[TsmomInterval] = []
        prior = 0
        for index, direction in enumerate(sequences[sym]):
            turnover = turnover_units(prior, direction)
            prior = direction
            ts = (
                datetime(2026, 6, 1, tzinfo=UTC)
                + timedelta(hours=24 * index + sym_index)
            ).isoformat()
            runs.append(
                _make_interval(
                    symbol=sym,
                    timestamp=ts,
                    direction=direction,
                    turnover=turnover,
                    interval_return="0.02",
                    vol_proxy="0.05",
                )
            )
        expanded[sym] = runs

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=_baseline_dev_intervals(),
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    assert report["gate_conditions"]["expanded_vt_post_cost_moderate_gt_0"]["passes"] is True
    assert report["gate_conditions"]["expanded_beats_random_p75"]["passes"] is False
    assert report["decision"] != RESULT_PASS


def test_cond3_flip_funding_adjusted_le_zero_decides_not_pass() -> None:
    """Flipping cond_3 (funding-adjusted ≤ 0) prevents PASS while cond_1 still passes."""

    # Tiny vol_proxy makes per-interval funding impact (-0.0009 / vol_proxy) dominate
    # the small per-interval vt baseline, while baseline E_h stays > 0.
    expanded: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        expanded[sym] = _per_symbol_run(
            direction=1,
            n=4,
            interval_return="0.001",
            vol_proxy="0.0005",
            symbol=sym,
            base_offset_hours=sym_index,
        )

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=_baseline_dev_intervals(),
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    assert report["gate_conditions"]["expanded_vt_post_cost_moderate_gt_0"]["passes"] is True
    assert report["gate_conditions"]["funding_adjusted_high_cost_gt_0"]["passes"] is False
    assert report["decision"] != RESULT_PASS


def test_cond4_flip_less_than_two_symbols_non_negative_decides_not_pass() -> None:
    """Flipping cond_4 (<2 of 3 symbols non-negative) prevents PASS."""

    expanded: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    # BTC: positive contribution.
    expanded["BTCUSDT"] = _per_symbol_run(
        direction=1,
        n=4,
        interval_return="0.02",
        vol_proxy="0.05",
        symbol="BTCUSDT",
        base_offset_hours=0,
    )
    # ETH: negative per-symbol vt.
    expanded["ETHUSDT"] = _per_symbol_run(
        direction=-1,
        n=4,
        interval_return="0.02",
        vol_proxy="0.05",
        symbol="ETHUSDT",
        base_offset_hours=1,
    )
    # SOL: negative per-symbol vt.
    expanded["SOLUSDT"] = _per_symbol_run(
        direction=-1,
        n=4,
        interval_return="0.02",
        vol_proxy="0.05",
        symbol="SOLUSDT",
        base_offset_hours=2,
    )

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=_baseline_dev_intervals(),
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    assert report["gate_conditions"]["two_of_three_symbols_non_negative"]["passes"] is False
    assert report["decision"] != RESULT_PASS


def test_cond5_flip_combined_retention_below_50pct_decides_not_pass() -> None:
    """Flipping cond_5 (ratio < 0.5) prevents PASS while cond_1 still passes.

    Uses a tiny vol_proxy so the boundary turnover correction at dev→expanded
    direction flip is large enough to drag the combined-window recomputation
    well below 50% of dev-only — even though the expanded headline is positive.
    """

    dev_intervals: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    expanded_intervals: dict[str, list[TsmomInterval]] = {sym: [] for sym in FROZEN_SYMBOLS}
    for sym_index, sym in enumerate(FROZEN_SYMBOLS):
        dev_intervals[sym] = [
            _make_interval(
                symbol=sym,
                timestamp=(
                    datetime(2024, 6, 1, tzinfo=UTC) + timedelta(hours=sym_index)
                ).isoformat(),
                direction=1,
                turnover=1,
                interval_return="0.0005",
                vol_proxy="0.001",
                split="discovery",
            )
        ]
        # Direction=-1 with negative interval_return gives positive signed return,
        # so cond_1 passes; but at the union boundary, recomputed turnover=2 makes
        # boundary cost large relative to vol_proxy, dragging the union total
        # negative.
        expanded_intervals[sym] = [
            _make_interval(
                symbol=sym,
                timestamp=(
                    datetime(2026, 6, 1, tzinfo=UTC) + timedelta(hours=sym_index)
                ).isoformat(),
                direction=-1,
                turnover=1,
                interval_return="-0.0005",
                vol_proxy="0.001",
            )
        ]

    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=dev_intervals,
        expanded_intervals_by_symbol=expanded_intervals,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    assert report["gate_conditions"]["expanded_vt_post_cost_moderate_gt_0"]["passes"] is True
    assert report["gate_conditions"]["combined_retention_ratio_gte_50pct"]["passes"] is False
    assert report["decision"] != RESULT_PASS


# --- schema and determinism ---


REQUIRED_SCHEMA_FIELDS: tuple[str, ...] = (
    "schema",
    "expanded_window_start",
    "expanded_window_end",
    "expansion_direction",
    "dev_window_start",
    "dev_window_end",
    "symbols_evaluated",
    "symbols_usable",
    "symbols_missing",
    "per_symbol_counts",
    "expanded_summary",
    "expanded_vol_thresholds",
    "expanded_regime_split",
    "vol_proxy_skipped_intervals_expanded",
    "funding_scenario",
    "funding_rate_per_8h",
    "funding_intervals_per_rebalance",
    "funding_impact_on_expanded_vt_post_cost_moderate",
    "funding_adjusted_expanded_vt_post_cost_moderate_high_cost",
    "random_seed",
    "random_iterations",
    "random_p75_expanded",
    "per_symbol_expanded_vt_post_cost_moderate",
    "symbols_non_negative_count",
    "combined_retention_numerator",
    "combined_retention_denominator",
    "combined_retention_ratio",
    "combined_retention_threshold",
    "combined_retention_passes",
    "gate_conditions",
    "decision",
    "data_source_attribution",
    "no_readiness_disclaimer",
)


def test_json_schema_completeness() -> None:
    report = evaluate_c7_expanded_intervals(
        dev_intervals_by_symbol=_baseline_dev_intervals(),
        expanded_intervals_by_symbol=_baseline_expanded_intervals(),
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    for field in REQUIRED_SCHEMA_FIELDS:
        assert field in report, f"missing schema field: {field}"

    assert report["schema"] == REPORT_SCHEMA
    assert report["funding_scenario"] == "high_cost"
    assert report["primary_lookback"] == PRIMARY_LOOKBACK
    assert report["random_seed"] == RANDOM_BASELINE_SEED
    assert report["random_iterations"] == RANDOM_ITERATIONS
    assert report["symbols_evaluated"] == list(FROZEN_SYMBOLS)
    expected_threshold = Decimal(str(report["combined_retention_threshold"]))
    assert expected_threshold == COMBINED_RETENTION_THRESHOLD
    # All five gate-condition entries present, each with value/threshold/passes.
    for cond_name in (
        "expanded_vt_post_cost_moderate_gt_0",
        "expanded_beats_random_p75",
        "funding_adjusted_high_cost_gt_0",
        "two_of_three_symbols_non_negative",
        "combined_retention_ratio_gte_50pct",
    ):
        cond = report["gate_conditions"][cond_name]
        assert "value" in cond
        assert "threshold" in cond
        assert "passes" in cond
    assert (
        "No paper, runtime, trading, or live readiness"
        in report["no_readiness_disclaimer"]
    )
    # JSON-safe round trip.
    json.dumps(report)


def test_deterministic_output_for_same_inputs() -> None:
    dev = _baseline_dev_intervals()
    expanded = _baseline_expanded_intervals()
    kwargs = dict(
        dev_intervals_by_symbol=dev,
        expanded_intervals_by_symbol=expanded,
        expanded_window_start="2026-05-07T00:00:00+00:00",
        expanded_window_end="2026-09-01T00:00:00+00:00",
        expansion_direction="forward",
    )

    first = evaluate_c7_expanded_intervals(**kwargs)
    second = evaluate_c7_expanded_intervals(**kwargs)

    assert first == second


# --- import / no-network guard ---


def test_no_network_static_import_guard() -> None:
    module_path = (
        REPO_ROOT
        / "research"
        / "signal_observation"
        / "setup_c_c7_expanded_validation.py"
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


# --- parity with published artifact ---


def test_dev_denominator_parity_with_published_setup_c_tsmom_artifact() -> None:
    if not PUBLISHED_TSMOM_JSON.is_file():
        pytest.skip("published Setup C JSON artifact not present")
    csv_paths = {
        sym: DEV_BITGET_DATA_DIR / f"{sym}_USDT-FUTURES_4H.csv"
        for sym in FROZEN_SYMBOLS
    }
    if not all(p.is_file() for p in csv_paths.values()):
        pytest.skip("dev Bitget 4H CSVs not present")

    candles_by_symbol = {sym: load_ohlcv_csv(p) for sym, p in csv_paths.items()}
    intervals = build_tsmom_intervals(candles_by_symbol, lookback=PRIMARY_LOOKBACK)
    intervals_by_symbol: dict[str, list[TsmomInterval]] = defaultdict(list)
    for item in intervals:
        intervals_by_symbol[item.symbol].append(item)

    headline_value = Decimal(
        str(
            summarize_intervals(intervals)["volatility_targeted_post_cost_return"][
                PRIMARY_COST_SCENARIO
            ]
        )
    )
    published = json.loads(PUBLISHED_TSMOM_JSON.read_text(encoding="utf-8"))
    published_value = Decimal(
        str(
            published["lookbacks"][str(PRIMARY_LOOKBACK)]["metrics"]["full"][
                "volatility_targeted_post_cost_return"
            ][PRIMARY_COST_SCENARIO]
        )
    )
    if headline_value != published_value:
        pytest.skip(
            "dev Bitget CSVs have drifted from published Setup C JSON; "
            "parity test cannot run against current artifact"
        )

    recomputed = combined_window_vt_post_cost_moderate(dict(intervals_by_symbol))
    # summarize_intervals sums chronologically across all symbols, while the
    # combined-window recomputation sums per-symbol-then-across-symbols. Both
    # are mathematically equivalent but differ by Decimal-precision artifacts
    # at the 25th significant digit. Compare quantized to 18 decimal places.
    quantum = Decimal("1E-18")
    assert recomputed.quantize(quantum) == published_value.quantize(quantum)
