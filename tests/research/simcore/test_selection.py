"""Tests for research/simcore/selection.py (spec Phase 1)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from research.simcore.models import Direction, FillPolicy, TargetSim, TradeSim, TradeSpec
from research.simcore.selection import select_non_overlapping


def _spec(symbol: str = "X", signal_index: int = 0) -> TradeSpec:
    return TradeSpec(
        symbol=symbol,
        direction=Direction.LONG,
        signal_index=signal_index,
        stop_price=Decimal("90"),
        target_r_values=(Decimal("1"),),
        outcome_window_bars=10,
    )


def _sim(symbol: str, entry_idx: int, exit_idx: int, target_r: Decimal = Decimal("1")) -> TradeSim:
    target_sim = TargetSim(
        target_r=target_r,
        target_price=Decimal("110"),
        outcome="win",
        exit_price=Decimal("110"),
        exit_index=exit_idx,
        bars_to_resolution=exit_idx - entry_idx + 1,
        gap_exit=False,
        final_r_gross=Decimal("1"),
        mae_r=Decimal("0"),
        mfe_r=Decimal("1"),
    )
    return TradeSim(
        spec=_spec(symbol=symbol, signal_index=max(0, entry_idx - 1)),
        entry_index=entry_idx,
        entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        entry_price=Decimal("100"),
        initial_r=Decimal("10"),
        session="Asia",
        targets={target_r: target_sim},
    )


def test_single_sim_always_kept():
    result = select_non_overlapping([_sim("X", 0, 4)], target_r=Decimal("1"))
    assert len(result) == 1
    assert result[0].entry_index == 0


def test_non_overlapping_both_kept():
    # sim1 exit=4, sim2 entry=5 > 4 → both kept
    result = select_non_overlapping([_sim("X", 0, 4), _sim("X", 5, 9)], target_r=Decimal("1"))
    assert len(result) == 2


def test_overlapping_second_dropped():
    # sim1 exit=4, sim2 entry=3 ≤ 4 → sim2 dropped
    result = select_non_overlapping([_sim("X", 0, 4), _sim("X", 3, 7)], target_r=Decimal("1"))
    assert len(result) == 1
    assert result[0].entry_index == 0


def test_three_sims_middle_dropped():
    # sim1 exit=4, sim2 entry=3 ≤ 4 → dropped; sim3 entry=6 > 4 → kept
    result = select_non_overlapping(
        [_sim("X", 0, 4), _sim("X", 3, 5), _sim("X", 6, 8)],
        target_r=Decimal("1"),
    )
    assert [s.entry_index for s in result] == [0, 6]


def test_adjacent_entry_equals_exit_dropped():
    # entry == exit → NOT strictly greater than → dropped
    result = select_non_overlapping([_sim("X", 0, 5), _sim("X", 5, 9)], target_r=Decimal("1"))
    assert len(result) == 1
    assert result[0].entry_index == 0


def test_entry_one_past_exit_kept():
    # entry = exit + 1 → strictly greater → kept
    result = select_non_overlapping([_sim("X", 0, 5), _sim("X", 6, 9)], target_r=Decimal("1"))
    assert len(result) == 2


def test_different_symbols_independent():
    # sim A and sim B (different symbols) do not filter each other
    sim_a = _sim("A", 0, 10)
    sim_b = _sim("B", 0, 10)
    result = select_non_overlapping([sim_a, sim_b], target_r=Decimal("1"))
    assert len(result) == 2


def test_target_r_not_in_sim_skipped():
    # sim has 1R target; querying for 2R → sim skipped (no KeyError)
    result = select_non_overlapping([_sim("X", 0, 4)], target_r=Decimal("2"))
    assert result == []


def test_empty_input():
    assert select_non_overlapping([], target_r=Decimal("1")) == []


def test_preserves_order_sorted_by_entry():
    # Input reversed: sim3 before sim1. Output must be sorted by entry_index.
    result = select_non_overlapping(
        [_sim("X", 6, 8), _sim("X", 0, 4)],
        target_r=Decimal("1"),
    )
    assert [s.entry_index for s in result] == [0, 6]
