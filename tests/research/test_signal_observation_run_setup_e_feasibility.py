"""Tests for run_setup_e_feasibility — synthetic CSVs, no network, no outcome metrics."""
from __future__ import annotations

import csv
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research.signal_observation.run_setup_e_feasibility import (
    _load_liquidation_csv,
    count_cascade_episodes,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = datetime(2024, 1, 1, tzinfo=UTC)
_4H = timedelta(hours=4)


def _write_ohlcv_csv(path: Path, bars: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for b in bars:
            ts = b["timestamp"].isoformat().replace("+00:00", "Z")
            w.writerow([ts, b["open"], b["high"], b["low"], b["close"], b.get("volume", 1000)])
    return path


def _write_liq_csv(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp_utc", "long_notional_usd", "short_notional_usd"])
        for r in rows:
            ts = r["timestamp"].isoformat().replace("+00:00", "Z")
            w.writerow([ts, r["long"], r.get("short", 0)])
    return path


def _flat_bars(n: int, *, liq_long: float = 100_000.0) -> tuple[list[dict], list[dict]]:
    """Generate n flat 4H bars and matching liquidation rows with constant notional."""
    ohlcv = []
    liq = []
    for i in range(n):
        ts = _BASE + i * _4H
        ohlcv.append({
            "timestamp": ts, "open": Decimal("100"), "high": Decimal("101"),
            "low": Decimal("99"), "close": Decimal("100"), "volume": Decimal("1000"),
        })
        liq.append({"timestamp": ts, "long": Decimal(str(liq_long)), "short": Decimal("50000")})
    return ohlcv, liq


# ---------------------------------------------------------------------------
# Test: liquidation CSV loader
# ---------------------------------------------------------------------------

def test_load_liquidation_csv_parses_rows(tmp_path):
    liq_path = tmp_path / "test_liq.csv"
    rows = [
        {"timestamp": _BASE, "long": Decimal("500000"), "short": Decimal("300000")},
        {"timestamp": _BASE + _4H, "long": Decimal("600000"), "short": Decimal("200000")},
    ]
    _write_liq_csv(liq_path, rows)
    loaded = _load_liquidation_csv(liq_path)
    assert len(loaded) == 2
    assert loaded[0]["long"] == Decimal("500000")
    assert loaded[1]["short"] == Decimal("200000")
    assert loaded[0]["timestamp"].tzinfo is not None


def test_load_liquidation_csv_missing_column_raises(tmp_path):
    bad_path = tmp_path / "bad.csv"
    with bad_path.open("w") as fh:
        fh.write("timestamp_utc,long_notional_usd\n2024-01-01T00:00:00Z,100\n")
    with pytest.raises(ValueError, match="short_notional_usd"):
        _load_liquidation_csv(bad_path)


# ---------------------------------------------------------------------------
# Test: episode counting — no outcome metrics
# ---------------------------------------------------------------------------

def test_episode_count_zero_on_uniform_liq():
    """Constant liquidation never exceeds 95th percentile → no cascade bars → 0 episodes."""
    ohlcv, liq = _flat_bars(300)
    result = count_cascade_episodes(ohlcv, liq)
    # No cascade bar can fire when all values are identical
    assert result["episodes"] == 0
    assert result["cascade_bars"] == 0


def test_episode_count_detects_clear_cascade_and_exhaustion():
    """Inject one large long-liq spike (down bar) followed by a low-liq bar."""
    # Hand-derived:
    # bars 0..179: baseline long=100_000; bar 180: long=5_000_000 (spike), down bar
    # bar 181: long=50_000 (< trailing median ~100_000) → exhaustion → 1 episode
    n_base = 190
    ohlcv, liq = _flat_bars(n_base)
    # Inject cascade at bar 180
    ohlcv[180]["open"] = Decimal("102")
    ohlcv[180]["close"] = Decimal("98")  # down bar
    liq[180]["long"] = Decimal("5000000")  # far above 95th percentile
    # Inject exhaustion at bar 181 (long below trailing median)
    liq[181]["long"] = Decimal("1000")  # well below median

    result = count_cascade_episodes(ohlcv, liq)
    assert result["cascade_bars"] >= 1
    assert result["episodes"] == 1


def test_episode_count_does_not_compute_forward_returns():
    """Episode counting returns only counts and bar ranges — no price-based metrics."""
    ohlcv, liq = _flat_bars(300)
    result = count_cascade_episodes(ohlcv, liq)
    # The result must NOT contain any forward-price metric keys
    forbidden_keys = {"return", "win_rate", "expectancy", "mae", "mfe", "final_r", "pnl"}
    for key in result:
        assert key.lower() not in forbidden_keys, (
            f"count_cascade_episodes returned a forbidden outcome key: {key!r}"
        )


def test_episodes_non_overlapping():
    """Two cascade bars close together produce at most one episode (constitution §3.8)."""
    n_base = 220
    ohlcv, liq = _flat_bars(n_base)
    # Two cascades at bars 180 and 182 (one 4H bar apart)
    for idx in (180, 182):
        ohlcv[idx]["open"] = Decimal("102")
        ohlcv[idx]["close"] = Decimal("98")
        liq[idx]["long"] = Decimal("5000000")
    # Exhaustion at bar 181
    liq[181]["long"] = Decimal("1000")

    result = count_cascade_episodes(ohlcv, liq)
    # Because bar 182 cascade starts while bar 180's episode is unresolved,
    # only one episode should be counted
    assert result["episodes"] <= 1


# ---------------------------------------------------------------------------
# Test: main() CLI
# ---------------------------------------------------------------------------

def test_main_no_data_dir_returns_2(tmp_path):
    rc = main(["--data-dir", str(tmp_path / "nonexistent")])
    assert rc == 2


def test_main_writes_feasibility_report(tmp_path):
    ohlcv, liq = _flat_bars(300)
    _write_ohlcv_csv(tmp_path / "SYM_ohlcv_4h.csv", ohlcv)
    _write_liq_csv(tmp_path / "SYM_liquidation_4h.csv", liq)

    rc = main(["--data-dir", str(tmp_path)])
    assert rc in (0, 1)

    report_path = tmp_path / "feasibility_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())

    assert "total_signal_episodes" in report
    assert "symbols" in report
    assert len(report["symbols"]) == 1
    # Verify no outcome metric keys in the report
    sym = report["symbols"][0]
    for key in sym:
        assert key.lower() not in {"return", "win_rate", "expectancy", "pnl"}, (
            f"Forbidden outcome metric key in report: {key!r}"
        )
    # Must include the hard-rule note
    assert "HARD RULE" in report.get("note", "")
