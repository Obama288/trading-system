"""Golden tests G1–G14 for research/simcore (spec §8, Phase 1).

Every expected value is derived by hand in the comment above the assertion.
NEVER regenerate expectations by running the new code; update manually with
the derivation shown.

Candle fixture convention
-------------------------
All tests use 4-hour bars starting at BASE_TS (2024-01-01 00:00 UTC, Monday).
H4 = timedelta(hours=4).  bar(n, o, h, l, c) builds candles[n] at n*H4.

Standard setup used by G1-G5 unless stated otherwise:
  signal_index=0, direction=LONG, stop=96, 1R target=104
  entry_index=1, entry_price=100 (candles[1].open), initial_r=4
  target_price = 100 + 1*4 = 104

Session note: decision_time(candles[0], H4) = BASE_TS + 4h = 04:00 UTC
  → signal_observation.sessions.session_label → hour=4 < 8 → "Asia"
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from research.simcore.candles import Candle
from research.simcore.costs import SCENARIOS, cost_in_r
from research.simcore.models import Direction, FillPolicy, InvalidTrade, TradeSim, TradeSpec
from research.simcore.selection import select_non_overlapping
from research.simcore.simulator import simulate_trade
from research.simcore.timeutil import bar_duration

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

BASE_TS = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
H4 = timedelta(hours=4)


def _c(n: int, o: str, h: str, l: str, c: str, v: str = "1000") -> Candle:
    """Build candle at offset n*H4 from BASE_TS."""
    return Candle(
        timestamp=BASE_TS + n * H4,
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(l),
        close=Decimal(c),
        volume=Decimal(v),
    )


def _spec(
    *,
    direction: Direction = Direction.LONG,
    signal_index: int = 0,
    stop: str = "96",
    targets: tuple[str, ...] = ("1",),
    window: int = 3,
    fill: FillPolicy = FillPolicy.NEXT_BAR_OPEN,
) -> TradeSpec:
    return TradeSpec(
        symbol="TEST",
        direction=direction,
        signal_index=signal_index,
        stop_price=Decimal(stop),
        target_r_values=tuple(Decimal(t) for t in targets),
        outcome_window_bars=window,
        fill=fill,
    )


def _make_sim_stub(symbol: str, entry_idx: int, exit_idx: int, target_r: Decimal = Decimal("1")) -> TradeSim:
    """Build a minimal TradeSim for selection tests (G12)."""
    from research.simcore.models import TargetSim

    spec = TradeSpec(
        symbol=symbol,
        direction=Direction.LONG,
        signal_index=max(0, entry_idx - 1),
        stop_price=Decimal("90"),
        target_r_values=(target_r,),
        outcome_window_bars=exit_idx - entry_idx + 1,
    )
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
        spec=spec,
        entry_index=entry_idx,
        entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        entry_price=Decimal("100"),
        initial_r=Decimal("10"),
        session="Asia",
        targets={target_r: target_sim},
    )


# ---------------------------------------------------------------------------
# G1 — LONG, target hit on bar 3 of window, no gaps
# ---------------------------------------------------------------------------
# candles[0] = signal bar (any values; close=100 referenced for context only)
# candles[1] = entry bar   o=100, h=102, l=99,  c=101   entry_price=100
# candles[2]              o=101, h=103, l=100, c=102
# candles[3]              o=102, h=105, l=101, c=104  ← target hit (h=105≥104)
#
# entry_price=100, stop=96, initial_r=|100-96|=4, target=100+1*4=104
#
# Bar-by-bar resolution:
#   bar1 (entry, gap-skip): l=99>96 ✓, h=102<104 ✓ → no exit
#   bar2: open=101>96 ✓, open<104 ✓; l=100>96 ✓, h=103<104 ✓ → no exit
#   bar3: open=102>96 ✓, open<104 ✓; l=101>96 ✓, h=105≥104 → WIN
#     exit_price=104, exit_index=3, bars_to_resolution=3-1+1=3
#     final_r_gross=(104-100)/4=4/4=1.0 (=target_r exactly)
#
# MAE over bars[1..3]: min_low=min(99,100,101)=99
#   mae_r=(100-99)/4=1/4=0.25
# MFE over bars[1..3]: max_high=max(102,103,105)=105
#   mfe_r=(105-100)/4=5/4=1.25

def test_g1_long_target_hit_bar3_no_gaps():
    candles = [
        _c(0, "99",  "100", "98",  "100"),  # signal bar
        _c(1, "100", "102", "99",  "101"),  # entry bar
        _c(2, "101", "103", "100", "102"),
        _c(3, "102", "105", "101", "104"),  # target hit
    ]
    result = simulate_trade(candles, _spec(), H4)

    assert isinstance(result, TradeSim)
    tr = result.targets[Decimal("1")]
    assert tr.outcome == "win"
    assert tr.exit_price == Decimal("104")
    assert tr.exit_index == 3
    assert tr.bars_to_resolution == 3
    assert tr.gap_exit is False
    assert tr.final_r_gross == Decimal("1")  # (104-100)/4 = 1 exactly
    assert result.entry_price == Decimal("100")
    assert result.initial_r == Decimal("4")
    assert result.session == "Asia"  # decision_time(bar0, 4H)=04:00 UTC → Asia


# ---------------------------------------------------------------------------
# G2 — LONG, stop and target both intrabar-reachable: stop takes priority
# ---------------------------------------------------------------------------
# candles[1] = entry bar  o=100, h=105, l=93, c=99
#   h=105≥104 (target) AND l=93≤96 (stop) — both reachable
#
# Spec §5.3 step 2: stop is evaluated BEFORE target (constitution §3.4).
#
#   exit_price=96, outcome="loss", exit_index=1, bars_to_resolution=1
#   final_r_gross=(96-100)/4=-4/4=-1.0
#
# MAE over bars[1..1]: min_low=93
#   mae_r=(100-93)/4=7/4=1.75
# MFE over bars[1..1]: max_high=105
#   mfe_r=(105-100)/4=5/4=1.25

def test_g2_long_stop_priority_over_target_intrabar():
    candles = [
        _c(0, "99",  "100", "98",  "100"),
        _c(1, "100", "105", "93",  "99"),  # both levels reachable
        _c(2, "99",  "102", "98",  "101"),
        _c(3, "101", "103", "100", "102"),
    ]
    result = simulate_trade(candles, _spec(), H4)

    assert isinstance(result, TradeSim)
    tr = result.targets[Decimal("1")]
    assert tr.outcome == "loss"
    assert tr.exit_price == Decimal("96")
    assert tr.exit_index == 1
    assert tr.bars_to_resolution == 1
    assert tr.gap_exit is False
    assert tr.final_r_gross == Decimal("-1")  # (96-100)/4 exactly
    assert tr.mae_r == Decimal("7") / Decimal("4")   # (100-93)/4 = 1.75
    assert tr.mfe_r == Decimal("5") / Decimal("4")   # (105-100)/4 = 1.25


# ---------------------------------------------------------------------------
# G3 — LONG, bar2 opens below stop → gap loss, final_r < −1
# ---------------------------------------------------------------------------
# candles[1] = entry bar   o=100, h=101, l=99,  c=100
# candles[2]              o=92,  h=93,  l=91,  c=92   opens below stop=96
#
# Bar-by-bar:
#   bar1 (entry, gap-skip): l=99>96 ✓, h=101<104 ✓ → no exit
#   bar2: gap check LONG: open=92 ≤ stop=96 → GAP LOSS
#     exit_price=92, exit_index=2, gap_exit=True, bars_to_resolution=2
#     final_r_gross=(92-100)/4=-8/4=-2.0  (< −1 as required)
#
# MAE over bars[1..2]: min_low=min(99,91)=91
#   mae_r=(100-91)/4=9/4=2.25
# MFE over bars[1..2]: max_high=max(101,93)=101
#   mfe_r=(101-100)/4=1/4=0.25

def test_g3_long_gap_below_stop():
    candles = [
        _c(0, "99",  "100", "98",  "100"),
        _c(1, "100", "101", "99",  "100"),  # entry bar
        _c(2, "92",  "93",  "91",  "92"),   # gap below stop
    ]
    result = simulate_trade(candles, _spec(window=2), H4)

    assert isinstance(result, TradeSim)
    tr = result.targets[Decimal("1")]
    assert tr.outcome == "loss"
    assert tr.exit_price == Decimal("92")
    assert tr.exit_index == 2
    assert tr.bars_to_resolution == 2
    assert tr.gap_exit is True
    assert tr.final_r_gross == Decimal("-2")  # (92-100)/4 = -8/4 = -2 exactly
    assert tr.final_r_gross < Decimal("-1")   # confirmed < -1
    assert tr.mae_r == Decimal("9") / Decimal("4")  # (100-91)/4 = 2.25
    assert tr.mfe_r == Decimal("1") / Decimal("4")  # (101-100)/4 = 0.25


# ---------------------------------------------------------------------------
# G4 — SHORT mirror of G3 (symmetric values)
# ---------------------------------------------------------------------------
# SHORT: entry=100, stop=104 (above), initial_r=|100-104|=4, 1R target=96
#
# candles[1] = entry bar  o=100, h=101, l=99, c=100
#   SHORT intrabar: h=101≥104? No.  l=99≤96? No. No exit.
# candles[2]             o=108, h=109, l=107, c=108  opens above stop=104
#   gap check SHORT: open=108 ≥ stop=104 → GAP LOSS
#     exit_price=108, exit_index=2, gap_exit=True, bars_to_resolution=2
#     final_r_gross=(100-108)/4=-8/4=-2.0  (< −1, symmetric with G3)
#
# MAE SHORT over bars[1..2]: adverse = highs above entry
#   max_high=max(101,109)=109  mae_r=(109-100)/4=9/4=2.25  ← symmetric
# MFE SHORT over bars[1..2]: favourable = lows below entry
#   min_low=min(99,107)=99   mfe_r=(100-99)/4=1/4=0.25   ← symmetric

def test_g4_short_gap_above_stop_mirror_of_g3():
    candles = [
        _c(0, "101", "102", "99",  "101"),
        _c(1, "100", "101", "99",  "100"),  # entry bar
        _c(2, "108", "109", "107", "108"),  # gap above stop
    ]
    result = simulate_trade(
        candles,
        _spec(direction=Direction.SHORT, stop="104", targets=("1",), window=2),
        H4,
    )

    assert isinstance(result, TradeSim)
    assert result.initial_r == Decimal("4")  # |100-104|
    tr = result.targets[Decimal("1")]
    assert tr.outcome == "loss"
    assert tr.exit_price == Decimal("108")
    assert tr.gap_exit is True
    assert tr.final_r_gross == Decimal("-2")  # (100-108)/4 = -2 (symmetric with G3)
    assert tr.mae_r == Decimal("9") / Decimal("4")  # symmetric with G3
    assert tr.mfe_r == Decimal("1") / Decimal("4")  # symmetric with G3


# ---------------------------------------------------------------------------
# G5 — No level touched in window → flat, MTM at last close
# ---------------------------------------------------------------------------
# candles[1]=entry o=100, h=102, l=99,  c=101
# candles[2]       o=101, h=103, l=100, c=102
# candles[3]       o=102, h=103, l=101, c=102.5  ← last bar (h<104, l>96)
#
# None of the 3 window bars touches stop(96) or target(104).
# Flat at last close = 102.5
#   final_r_gross=(102.5-100)/4=2.5/4=0.625
#   exit_index=3, bars_to_resolution=3
#
# MAE over bars[1..3]: min_low=min(99,100,101)=99
#   mae_r=(100-99)/4=0.25
# MFE over bars[1..3]: max_high=max(102,103,103)=103
#   mfe_r=(103-100)/4=3/4=0.75

def test_g5_flat_no_level_touched():
    candles = [
        _c(0, "99",   "100", "98",   "100"),
        _c(1, "100",  "102", "99",   "101"),
        _c(2, "101",  "103", "100",  "102"),
        _c(3, "102",  "103", "101",  "102.5"),
    ]
    result = simulate_trade(candles, _spec(), H4)

    assert isinstance(result, TradeSim)
    tr = result.targets[Decimal("1")]
    assert tr.outcome == "flat"
    assert tr.exit_price == Decimal("102.5")
    assert tr.exit_index == 3
    assert tr.bars_to_resolution == 3
    assert tr.gap_exit is False
    # (102.5-100)/4 = 2.5/4 = 0.625 exactly in Decimal
    assert tr.final_r_gross == Decimal("2.5") / Decimal("4")
    assert tr.mae_r == Decimal("1") / Decimal("4")   # (100-99)/4
    assert tr.mfe_r == Decimal("3") / Decimal("4")   # (103-100)/4


# ---------------------------------------------------------------------------
# G6 — Entry bar open at/beyond stop → InvalidTrade entry_gap_through_stop
# ---------------------------------------------------------------------------
# NEXT_BAR_OPEN, LONG, stop=96
# candles[1] (entry bar): o=94 ≤ stop=96 → gap through stop, don't enter
# initial_r=|94-96|=2 would be positive but the open is at/below stop first.

def test_g6_entry_gap_through_stop():
    candles = [
        _c(0, "99",  "100", "98",  "99"),   # signal bar
        _c(1, "94",  "95",  "93",  "94"),   # entry bar opens below stop
        _c(2, "94",  "97",  "93",  "96"),
    ]
    result = simulate_trade(candles, _spec(), H4)

    assert isinstance(result, InvalidTrade)
    assert result.reason == "entry_gap_through_stop"


# ---------------------------------------------------------------------------
# G7 — Entry bar open at/beyond nearest target → InvalidTrade
#       Uses SIGNAL_CLOSE so that entry_bar.open ≠ entry_price
# ---------------------------------------------------------------------------
# SIGNAL_CLOSE, LONG, stop=96, 1R target
# candles[1] = signal/entry bar: o=110, h=112, l=98, c=100
#   entry_price = close = 100
#   initial_r = |100-96| = 4
#   nearest_target = 100+1*4=104
#   entry_bar.open=110 ≥ 104 → entry_gap_through_target

def test_g7_entry_gap_through_nearest_target_signal_close():
    candles = [
        _c(0, "99",  "100", "98",  "99"),    # placeholder
        _c(1, "110", "112", "98",  "100"),   # signal bar; open=110 >> target=104
        _c(2, "100", "104", "99",  "103"),
        _c(3, "102", "105", "100", "104"),
    ]
    result = simulate_trade(
        candles,
        _spec(signal_index=1, fill=FillPolicy.SIGNAL_CLOSE),
        H4,
    )

    assert isinstance(result, InvalidTrade)
    assert result.reason == "entry_gap_through_target"


# ---------------------------------------------------------------------------
# G8 — signal_index is last candle → InvalidTrade no_entry_bar
# ---------------------------------------------------------------------------
# NEXT_BAR_OPEN: entry_index = signal_index+1 = 2 ≥ len(candles)=2

def test_g8_no_entry_bar():
    candles = [
        _c(0, "99", "100", "98", "100"),
        _c(1, "100", "102", "99", "101"),  # signal_index = 1 = last index
    ]
    result = simulate_trade(candles, _spec(signal_index=1), H4)

    assert isinstance(result, InvalidTrade)
    assert result.reason == "no_entry_bar"


# ---------------------------------------------------------------------------
# G9 — Multi-target: 1R wins on bar 2, 2R flats at bar 3
# ---------------------------------------------------------------------------
# entry_price=100, stop=96, initial_r=4
# 1R target=104, 2R target=108
#
# candles[1] = entry bar  o=100, h=102, l=99,  c=101  (h<104, l>96: no exit)
# candles[2]              o=101, h=105, l=100, c=104  h=105≥104 but h<108
#   For 1R: gap check open=101<104 ✓; intrabar h=105≥104 → WIN at bar2
#     exit_price=104, bars_to_resolution=2, final_r_gross=1.0
#   For 2R: no stop (l=100>96), no target (h=105<108) → continue
# candles[3]              o=104, h=107, l=103, c=106  h<108 → 2R not hit
#   For 2R: window exhausted → FLAT at close=106
#     exit_price=106, bars_to_resolution=3, final_r_gross=(106-100)/4=6/4=1.5
#
# Confirms each target is resolved independently over the same window.

def test_g9_multi_target_1r_wins_2r_flats():
    candles = [
        _c(0, "99",  "100", "98",  "100"),
        _c(1, "100", "102", "99",  "101"),
        _c(2, "101", "105", "100", "104"),  # 1R hit (h=105≥104); 2R not (h<108)
        _c(3, "104", "107", "103", "106"),  # 2R not hit; flat
    ]
    result = simulate_trade(
        candles,
        _spec(targets=("1", "2"), window=3),
        H4,
    )

    assert isinstance(result, TradeSim)
    one_r = result.targets[Decimal("1")]
    two_r = result.targets[Decimal("2")]

    # 1R: hit at bar2
    assert one_r.outcome == "win"
    assert one_r.exit_index == 2
    assert one_r.bars_to_resolution == 2
    assert one_r.final_r_gross == Decimal("1")  # (104-100)/4

    # 2R: flat at bar3
    assert two_r.outcome == "flat"
    assert two_r.exit_index == 3
    assert two_r.bars_to_resolution == 3
    # (106-100)/4 = 6/4 = 1.5
    assert two_r.final_r_gross == Decimal("6") / Decimal("4")


# ---------------------------------------------------------------------------
# G10 — MAE/MFE exact Decimal values (same candle path as G1)
# ---------------------------------------------------------------------------
# Reuses G1 setup explicitly to lock exact Decimal arithmetic.
#
# bars[1..3] (the resolution window):
#   bar1: l=99, h=102
#   bar2: l=100, h=103
#   bar3: l=101, h=105  ← target hit here
#
# LONG MAE = (entry - min_low) / initial_r = (100-99) / 4 = Decimal("1")/Decimal("4")
#          = Decimal("0.25")  — exact in base-10 Decimal
#
# LONG MFE = (max_high - entry) / initial_r = (105-100) / 4 = Decimal("5")/Decimal("4")
#          = Decimal("1.25")  — exact in base-10 Decimal

def test_g10_mae_mfe_exact_decimal():
    candles = [
        _c(0, "99",  "100", "98",  "100"),
        _c(1, "100", "102", "99",  "101"),
        _c(2, "101", "103", "100", "102"),
        _c(3, "102", "105", "101", "104"),
    ]
    result = simulate_trade(candles, _spec(), H4)

    assert isinstance(result, TradeSim)
    tr = result.targets[Decimal("1")]
    # MAE: (100-99)/4 = 0.25 exactly
    assert tr.mae_r == Decimal("0.25")
    # MFE: (105-100)/4 = 1.25 exactly
    assert tr.mfe_r == Decimal("1.25")
    # Confirm these are Decimal, not float
    assert isinstance(tr.mae_r, Decimal)
    assert isinstance(tr.mfe_r, Decimal)


# ---------------------------------------------------------------------------
# G11 — cost_in_r: entry=100, stop=99.5 → initial_r=0.5, 8 bps → 0.32R
# ---------------------------------------------------------------------------
# cost_in_r = (2 * 8 / 10000) * 100 / 0.5
#           = (16 / 10000) * 200
#           = 0.0016 * 200
#           = 0.32
# All Decimal arithmetic: Decimal("16")/Decimal("10000") = Decimal("0.0016"),
# Decimal("0.0016")*Decimal("100") = Decimal("0.16"),
# Decimal("0.16")/Decimal("0.5") = Decimal("0.32") exactly.

def test_g11_cost_in_r_tight_stop_8bps():
    result = cost_in_r(
        entry_price=Decimal("100"),
        initial_r=Decimal("0.5"),      # |100 - 99.5|
        bps_per_side=Decimal("8"),     # moderate scenario
    )
    assert result == Decimal("0.32")
    assert isinstance(result, Decimal)

    # Verify moderate scenario key maps to 8 bps
    assert SCENARIOS["moderate"] == Decimal("8")


# ---------------------------------------------------------------------------
# G12 — select_non_overlapping drops overlapping 2nd sim
# ---------------------------------------------------------------------------
# Three sims for symbol "X", 1R target:
#   sim1: entry_index=0, exit_index=4  ← kept; last_exit=4
#   sim2: entry_index=3, 3 ≤ 4 → dropped (not strictly greater than 4)
#   sim3: entry_index=6, 6 > 4 → kept
#
# Expected result: [sim1, sim3]

def test_g12_select_non_overlapping_drops_overlap():
    sim1 = _make_sim_stub("X", entry_idx=0, exit_idx=4)
    sim2 = _make_sim_stub("X", entry_idx=3, exit_idx=5)  # overlaps sim1 (3 ≤ 4)
    sim3 = _make_sim_stub("X", entry_idx=6, exit_idx=8)  # 6 > 4 → kept

    result = select_non_overlapping([sim1, sim2, sim3], target_r=Decimal("1"))

    assert len(result) == 2
    assert result[0].entry_index == 0
    assert result[1].entry_index == 6
    assert all(s.spec.symbol == "X" for s in result)


# ---------------------------------------------------------------------------
# G13 — SIGNAL_CLOSE result: gate_eligible must be False
# ---------------------------------------------------------------------------
# SIGNAL_CLOSE means diagnostic-only (spec §5.0 / constitution §3.2).
# TradeSim.gate_eligible returns True only for NEXT_BAR_OPEN fills.
#
# Setup: signal bar closes at 100, stop=96, target=104
# bar0 (signal/entry): o=99, h=102, l=98, c=100
#   gap-stop check: o=99>96 ✓   gap-target: o=99<104 ✓
#   intrabar: l=98>96 ✓, h=102<104 ✓ → no exit on entry bar
# bar1: o=101, h=106, l=100, c=105  h=106≥104 → WIN
# (Trade resolves normally; we just verify gate_eligible.)

def test_g13_signal_close_gate_eligible_false():
    candles = [
        _c(0, "99",  "102", "98",  "100"),  # signal bar; entry_price=close=100
        _c(1, "101", "106", "100", "105"),   # target hit (h=106≥104)
    ]
    result = simulate_trade(
        candles,
        _spec(fill=FillPolicy.SIGNAL_CLOSE, window=2),
        H4,
    )

    assert isinstance(result, TradeSim)
    # gate_eligible is False for SIGNAL_CLOSE fills
    assert result.gate_eligible is False
    assert result.spec.fill == FillPolicy.SIGNAL_CLOSE
    # Confirmed trade resolved (not InvalidTrade)
    tr = result.targets[Decimal("1")]
    assert tr.outcome == "win"


# ---------------------------------------------------------------------------
# G14 — bar_duration raises ValueError on mixed timeframes
# ---------------------------------------------------------------------------
# 4 candles: T, T+4h, T+8h, T+16h → deltas = [4h, 4h, 8h] in seconds
#   = [14400, 14400, 28800]
# median([14400, 14400, 28800]) = 14400
# max deviation: |28800-14400|/14400 = 14400/14400 = 1.0 > 0.01 → ValueError

def test_g14_bar_duration_raises_on_mixed_timeframes():
    candles = [
        _c(0, "100", "101", "99", "100"),
        _c(1, "101", "102", "100", "101"),
        _c(2, "102", "103", "101", "102"),
        # bar at offset 4 (T+16h) instead of T+12h — doubles the last interval
        Candle(
            timestamp=BASE_TS + timedelta(hours=16),
            open=Decimal("102"), high=Decimal("104"),
            low=Decimal("101"), close=Decimal("103"),
            volume=Decimal("1000"),
        ),
    ]
    with pytest.raises(ValueError, match="inconsistent"):
        bar_duration(candles)
