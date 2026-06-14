"""Tests for _acquire_setup_i — taker_buy/taker_sell aggregation semantics.

Canonical rule (aggtrades_downloader.py):
  isBuyerMaker=True  → aggressor is SELLER → taker_sell_vol (b[5])
  isBuyerMaker=False → aggressor is BUYER  → taker_buy_vol  (b[4])

bin layout: [open, high, low, close, taker_buy_vol, taker_sell_vol]
"""
from __future__ import annotations

import csv
import io
import tempfile
import zipfile
from pathlib import Path

import pytest

from research.signal_observation._acquire_setup_i import (
    _assert_flow_direction,
    _process_zip,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Hour 1 of UTC epoch: 1970-01-01T01:00:00Z = 3_600_000 ms
_HOUR1_MS = 3_600_000
# Ticks inside hour 1 — well below 10^15 so detected as milliseconds
_T1 = 3_601_000
_T2 = 3_602_000
_T3 = 3_603_000


def _make_zip(rows: list[list]) -> Path:
    """Write rows as a Binance-format aggTrades zip to a temp file; return path."""
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("BTCUSDT-aggTrades-2024-01.csv", buf.getvalue().encode())
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.write(zip_buf.getvalue())
    tmp.close()
    return Path(tmp.name)


def _row(ts: int, price: str, qty: str, ibm: str, agg_id: int = 1) -> list:
    """aggTrades row: agg_id, price, qty, first_id, last_id, ts, is_buyer_maker."""
    return [agg_id, price, qty, agg_id * 10, agg_id * 10 + 1, ts, ibm]


def _run(*rows) -> dict[int, list[float]]:
    path = _make_zip(list(rows))
    bins: dict[int, list[float]] = {}
    try:
        _process_zip(path, bins)
    finally:
        path.unlink(missing_ok=True)
    return bins


# ---------------------------------------------------------------------------
# Taker-volume assignment
# ---------------------------------------------------------------------------

class TestTakerVolumeAssignment:
    def test_buyer_maker_true_goes_to_taker_sell(self):
        """isBuyerMaker=True: buyer is passive maker → taker is SELLER → b[5]."""
        bins = _run(_row(_T1, "100.0", "5.0", "True"))
        b = bins[_HOUR1_MS]
        assert b[4] == 0.0, f"taker_buy_vol must be 0, got {b[4]}"
        assert b[5] == 5.0, f"taker_sell_vol must be 5.0, got {b[5]}"

    def test_buyer_maker_false_goes_to_taker_buy(self):
        """isBuyerMaker=False: buyer is aggressor → taker is BUYER → b[4]."""
        bins = _run(_row(_T1, "100.0", "3.0", "False"))
        b = bins[_HOUR1_MS]
        assert b[4] == 3.0, f"taker_buy_vol must be 3.0, got {b[4]}"
        assert b[5] == 0.0, f"taker_sell_vol must be 0, got {b[5]}"

    def test_mixed_ticks_accumulate_independently(self):
        """Buy-side and sell-side quantities accumulate into separate slots."""
        bins = _run(
            _row(_T1, "100.0", "5.0", "True",  agg_id=1),  # sell taker → b[5]
            _row(_T2, "101.0", "3.0", "False", agg_id=2),  # buy taker  → b[4]
            _row(_T3, "102.0", "2.0", "True",  agg_id=3),  # sell taker → b[5]
        )
        b = bins[_HOUR1_MS]
        assert b[0] == 100.0, f"open={b[0]}"
        assert b[1] == 102.0, f"high={b[1]}"
        assert b[2] == 100.0, f"low={b[2]}"
        assert b[3] == 102.0, f"close={b[3]}"
        assert b[4] == 3.0,   f"taker_buy_vol={b[4]}"   # only tick 2
        assert b[5] == 7.0,   f"taker_sell_vol={b[5]}"  # ticks 1+3

    def test_exact_values_not_zero_for_either_side(self):
        """Sanity: a single True tick leaves taker_buy at exactly 0, not noise."""
        bins = _run(_row(_T1, "50000.0", "0.001", "True"))
        b = bins[_HOUR1_MS]
        assert b[4] == 0.0
        assert abs(b[5] - 0.001) < 1e-12


# ---------------------------------------------------------------------------
# Flow-direction guard
# ---------------------------------------------------------------------------

class TestFlowDirectionGuard:
    def _up_bin(self, buy: float, sell: float) -> list[float]:
        """Bin: open=100, close=102.5 (2.5% → well above 0.2% threshold)."""
        return [100.0, 103.0, 99.0, 102.5, buy, sell]

    def test_passes_on_correct_data(self):
        """Net taker-buy in up-hours → no exception."""
        bins = {i: self._up_bin(10.0, 3.0) for i in range(60)}
        _assert_flow_direction(bins, "TESTUSDT")  # must not raise

    def test_raises_on_inverted_data(self):
        """Net taker-sell in up-hours → ValueError with inversion message."""
        bins = {i: self._up_bin(3.0, 10.0) for i in range(60)}
        with pytest.raises(ValueError, match="flow-direction sanity FAIL"):
            _assert_flow_direction(bins, "TESTUSDT")

    def test_silent_below_50_bars(self):
        """Fewer than 50 qualifying bars → guard is silent regardless of sign."""
        bins = {i: self._up_bin(3.0, 10.0) for i in range(49)}
        _assert_flow_direction(bins, "TESTUSDT")  # must not raise

    def test_ignores_flat_and_down_bars(self):
        """Down-move bars (close ≤ open*1.002) are not counted against the check."""
        # 60 inverted UP bars → would raise; but wrap them in down bars that dwarf them
        up_bins = {i: self._up_bin(3.0, 10.0) for i in range(49)}
        # Down bars: close < open, large net-sell (shouldn't matter to guard)
        down_bins = {100 + i: [100.0, 101.0, 98.0, 99.0, 1.0, 50.0] for i in range(200)}
        bins = {**up_bins, **down_bins}
        _assert_flow_direction(bins, "TESTUSDT")  # only 49 up-bars → silent
