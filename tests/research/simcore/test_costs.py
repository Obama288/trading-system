"""Tests for research/simcore/costs.py (spec Phase 1)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from research.simcore.costs import SCENARIOS, cost_in_r, final_r_net
from research.simcore.models import Direction, FillPolicy, TargetSim, TradeSpec


def _target_sim(
    outcome: str = "win",
    final_r_gross: str = "1",
) -> TargetSim:
    return TargetSim(
        target_r=Decimal("1"),
        target_price=Decimal("104"),
        outcome=outcome,
        exit_price=Decimal("104"),
        exit_index=2,
        bars_to_resolution=2,
        gap_exit=False,
        final_r_gross=Decimal(final_r_gross),
        mae_r=Decimal("0.25"),
        mfe_r=Decimal("1"),
    )


def test_scenarios_keys_and_values():
    assert set(SCENARIOS.keys()) == {"optimistic", "moderate", "conservative"}
    assert all(isinstance(v, Decimal) for v in SCENARIOS.values())
    assert SCENARIOS["optimistic"] == Decimal("5")
    assert SCENARIOS["moderate"] == Decimal("8")
    assert SCENARIOS["conservative"] == Decimal("15")


def test_cost_in_r_basic():
    # (2 * 8 / 10000) * 100 / 4 = 0.0016 * 25 = 0.04
    result = cost_in_r(
        entry_price=Decimal("100"),
        initial_r=Decimal("4"),
        bps_per_side=Decimal("8"),
    )
    assert result == Decimal("0.04")
    assert isinstance(result, Decimal)


def test_cost_in_r_tight_stop_magnifies():
    # (2 * 8 / 10000) * 100 / 0.5 = 0.0016 * 200 = 0.32
    result = cost_in_r(
        entry_price=Decimal("100"),
        initial_r=Decimal("0.5"),
        bps_per_side=Decimal("8"),
    )
    assert result == Decimal("0.32")


def test_cost_in_r_float_entry_price_raises():
    with pytest.raises(TypeError, match="entry_price"):
        cost_in_r(entry_price=100.0, initial_r=Decimal("4"), bps_per_side=Decimal("8"))  # type: ignore[arg-type]


def test_cost_in_r_float_initial_r_raises():
    with pytest.raises(TypeError, match="initial_r"):
        cost_in_r(entry_price=Decimal("100"), initial_r=4.0, bps_per_side=Decimal("8"))  # type: ignore[arg-type]


def test_cost_in_r_float_bps_raises():
    with pytest.raises(TypeError, match="bps_per_side"):
        cost_in_r(entry_price=Decimal("100"), initial_r=Decimal("4"), bps_per_side=8.0)  # type: ignore[arg-type]


def test_final_r_net_win():
    ts = _target_sim(outcome="win", final_r_gross="1")
    # cost=0.04: net = 1.0 - 0.04 = 0.96
    cost = cost_in_r(entry_price=Decimal("100"), initial_r=Decimal("4"), bps_per_side=Decimal("8"))
    assert final_r_net(ts, cost) == Decimal("1") - cost


def test_final_r_net_loss():
    ts = _target_sim(outcome="loss", final_r_gross="-1")
    cost = Decimal("0.04")
    # net = -1.0 - 0.04 = -1.04
    assert final_r_net(ts, cost) == Decimal("-1.04")


def test_final_r_net_returns_decimal():
    ts = _target_sim(final_r_gross="1.5")
    assert isinstance(final_r_net(ts, Decimal("0.1")), Decimal)
