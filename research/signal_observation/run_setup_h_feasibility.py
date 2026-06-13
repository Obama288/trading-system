"""Setup H Stage 1 feasibility runner.

Produces SETUP_H_FEASIBILITY_REPORT.md with:
- SHA-256 of each CSV
- Quality verdict per symbol
- Regime characterisation (LOW-VOL / HIGH-VOL rebalance bar counts)
- 70/30 discovery/validation split counts vs 80/40 minimums
- ZEC liquidity metrics (spread proxy + avg daily quote volume)
- FEASIBLE / NOT-FEASIBLE verdict

HARD RULE: no outcome metrics here — no returns, expectancy, Sharpe,
or anything derived from prices after a signal/rebalance bar.
Only data availability, quality, and COUNTS.

Run from project root:
    python -m research.signal_observation.run_setup_h_feasibility
"""
from __future__ import annotations

import hashlib
import statistics
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from research.signal_observation.csv_loader import load_ohlcv_csv
from research.signal_observation.indicators import atr
from research.simcore.quality import assess_candles, passes

DATA_DIR = ROOT / "research" / "signal_observation" / "data" / "setup_h"
REPORT_PATH = ROOT / "research" / "signal_observation" / "SETUP_H_FEASIBILITY_REPORT.md"

SYMBOLS = [
    "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", "ZECUSDT",
]

ATR_PERIOD = 20
REGIME_WINDOW = 180   # trailing-median window for ATR20/close
REBALANCE_EVERY = 6   # every 6th bar is a rebalance bar (0-indexed: 5, 11, 17...)
DISCOVERY_FRAC = 0.70

MIN_DISCOVERY_OBS = 80
MIN_VALIDATION_OBS = 40

# ZEC liquidity thresholds for include/exclude recommendation
ZEC_MIN_AVG_DAILY_QVOL_USD = 500_000   # $500k/day minimum to include
# HL/close ratio is a VOLATILITY proxy, not a bid-ask spread.
# Typical 4H crypto bar range is 1-6%. Values >8% flag extreme intrabar swings.
ZEC_HL_RANGE_EXTREME_PCT = 8.0


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _compute_regime(candles, *, atr_period: int, regime_window: int) -> list[str | None]:
    """Return per-bar regime label: 'LOW' | 'HIGH' | None (insufficient history)."""
    atr_vals = atr(candles, period=atr_period)
    n = len(candles)

    atr_vol = [None] * n
    for i in range(n):
        if atr_vals[i] is not None and candles[i].close > 0:
            atr_vol[i] = atr_vals[i] / candles[i].close

    regimes = [None] * n
    for i in range(n):
        if atr_vol[i] is None:
            continue
        window_start = i - (regime_window - 1)
        if window_start < 0:
            continue
        window = [atr_vol[j] for j in range(window_start, i + 1) if atr_vol[j] is not None]
        if len(window) < regime_window:
            continue
        med = Decimal(str(statistics.median(float(v) for v in window)))
        regimes[i] = "LOW" if atr_vol[i] < med else "HIGH"

    return regimes


def _count_regime_rebalance_bars(
    candles,
    regimes: list[str | None],
    cutoff_ts=None,
    *,
    side: str,
) -> tuple[int, int, int]:
    """Count LOW/HIGH regime rebalance bars for discovery or validation side.

    Returns (rebalance_total, low_vol, high_vol) where side='disc'|'val'.
    """
    total = low = high = 0
    for i, (c, r) in enumerate(zip(candles, regimes)):
        if i % REBALANCE_EVERY != (REBALANCE_EVERY - 1):
            continue  # not a rebalance bar
        if r is None:
            continue
        if cutoff_ts is not None:
            if side == "disc" and c.timestamp >= cutoff_ts:
                continue
            if side == "val" and c.timestamp < cutoff_ts:
                continue
        total += 1
        if r == "LOW":
            low += 1
        else:
            high += 1
    return total, low, high


def _zec_liquidity(candles) -> dict:
    from datetime import UTC
    days: dict[str, list] = {}
    for c in candles:
        d = c.timestamp.strftime("%Y-%m-%d")
        days.setdefault(d, []).append(c)

    daily_qvols = [
        float(sum(c.volume * c.close for c in dc))
        for dc in days.values()
    ]
    avg_qvol = sum(daily_qvols) / len(daily_qvols) if daily_qvols else 0.0

    hl_spreads = [
        float((c.high - c.low) / c.close * 100)
        for c in candles if c.close > 0
    ]
    avg_spread = sum(hl_spreads) / len(hl_spreads) if hl_spreads else 0.0

    return {
        "avg_daily_qvol_usd": round(avg_qvol, 0),
        "avg_hl_spread_pct": round(avg_spread, 4),
    }


def main() -> None:
    lines: list[str] = []
    emit = lines.append

    missing = [s for s in SYMBOLS if not (DATA_DIR / f"{s}_4h.csv").exists()]
    if missing:
        print(f"ERROR: missing CSV files for: {missing}")
        print("Run _acquire_setup_h.py first.")
        sys.exit(1)

    # --- load and hash all files ---
    file_hashes: dict[str, str] = {}
    candles_by_sym: dict[str, list] = {}
    quality_by_sym: dict[str, tuple[bool, list[str]]] = {}

    for sym in SYMBOLS:
        path = DATA_DIR / f"{sym}_4h.csv"
        file_hashes[sym] = _sha256_file(path)
        c = load_ohlcv_csv(path)
        candles_by_sym[sym] = c
        rpt = assess_candles(c)
        ok, reasons = passes(rpt)
        quality_by_sym[sym] = (ok, reasons)

    # combined dataset hash
    combined = hashlib.sha256(
        "".join(file_hashes[s] for s in sorted(SYMBOLS)).encode()
    ).hexdigest()

    # --- common date window for split ---
    starts = {s: candles_by_sym[s][0].timestamp for s in SYMBOLS}
    ends = {s: candles_by_sym[s][-1].timestamp for s in SYMBOLS}
    common_start = max(starts.values())
    common_end = min(ends.values())
    window_bars_approx = (common_end - common_start).days * 6  # 6 bars/day at 4H
    cutoff_approx = common_start + (common_end - common_start) * DISCOVERY_FRAC
    # Round to nearest 4H boundary
    cutoff_ts = common_start + timedelta(
        hours=4 * round((common_end - common_start).total_seconds() / 3600 * DISCOVERY_FRAC / 4)
    )

    # --- per-symbol regime ---
    regime_rows: list[dict] = []
    for sym in SYMBOLS:
        candles = candles_by_sym[sym]
        regimes = _compute_regime(candles, atr_period=ATR_PERIOD, regime_window=REGIME_WINDOW)
        d_total, d_low, d_high = _count_regime_rebalance_bars(
            candles, regimes, cutoff_ts, side="disc"
        )
        v_total, v_low, v_high = _count_regime_rebalance_bars(
            candles, regimes, cutoff_ts, side="val"
        )
        row = {
            "sym": sym,
            "bars": len(candles),
            "start": candles[0].timestamp.strftime("%Y-%m-%d"),
            "end": candles[-1].timestamp.strftime("%Y-%m-%d"),
            "quality_ok": quality_by_sym[sym][0],
            "d_total": d_total,
            "d_low": d_low,
            "d_high": d_high,
            "v_total": v_total,
            "v_low": v_low,
            "v_high": v_high,
        }
        if sym == "ZECUSDT":
            row["zec_liq"] = _zec_liquidity(candles)
        regime_rows.append(row)

    # --- verdict ---
    quality_fail = [r for r in regime_rows if not r["quality_ok"]]
    disc_fail = [r for r in regime_rows if r["d_total"] < MIN_DISCOVERY_OBS]
    val_fail = [r for r in regime_rows if r["v_total"] < MIN_VALIDATION_OBS]

    zec_row = next(r for r in regime_rows if r["sym"] == "ZECUSDT")
    zec_liq = zec_row.get("zec_liq", {})
    zec_include = (
        zec_liq.get("avg_daily_qvol_usd", 0) >= ZEC_MIN_AVG_DAILY_QVOL_USD
    )
    zec_extreme_volatility = zec_liq.get("avg_hl_spread_pct", 0) > ZEC_HL_RANGE_EXTREME_PCT

    all_pass = not quality_fail and not disc_fail and not val_fail
    verdict = "FEASIBLE" if all_pass else "NOT-FEASIBLE"

    # --- write report ---
    emit("# Setup H Feasibility Report")
    emit("")
    emit(f"Generated: {ROOT / 'research/signal_observation/run_setup_h_feasibility.py'}")
    emit(f"Data directory: `research/signal_observation/data/setup_h/`")
    emit("")
    emit(f"## Verdict: {verdict}")
    emit("")
    if quality_fail:
        emit(f"Quality failures: {[r['sym'] for r in quality_fail]}")
    if disc_fail:
        emit(f"Discovery minimum failures (< {MIN_DISCOVERY_OBS} obs): {[r['sym'] for r in disc_fail]}")
    if val_fail:
        emit(f"Validation minimum failures (< {MIN_VALIDATION_OBS} obs): {[r['sym'] for r in val_fail]}")
    if all_pass:
        emit(f"All {len(SYMBOLS)} symbols pass quality; all meet 80/40 rebalance-observation minimums.")
    emit("")
    emit("## Dataset SHA-256")
    emit("")
    emit(f"Combined hash (all files, sorted): `{combined}`")
    emit("")
    emit("Per-file hashes:")
    for sym in sorted(SYMBOLS):
        emit(f"- `{sym}`: `{file_hashes[sym]}`")
    emit("")
    emit("## Common date window (for 70/30 split)")
    emit("")
    emit(f"- Common start (latest first bar): `{common_start.strftime('%Y-%m-%d')}`")
    emit(f"- Common end (earliest last bar): `{common_end.strftime('%Y-%m-%d')}`")
    emit(f"- Discovery cutoff (~70%): `{cutoff_ts.strftime('%Y-%m-%d %H:%M UTC')}`")
    emit(f"- [TBD-F at lock: owner sets exact cutoff date from this estimate]")
    emit("")
    emit("## Coverage and quality")
    emit("")
    emit("| Symbol | Start | End | Bars | Quality |")
    emit("|--------|-------|-----|------|---------|")
    for r in regime_rows:
        q = "PASS" if r["quality_ok"] else f"FAIL"
        emit(f"| {r['sym']} | {r['start']} | {r['end']} | {r['bars']} | {q} |")
    emit("")
    emit("## Regime characterisation")
    emit("")
    emit(
        "Regime gate: ATR20/close < trailing 180-bar median = LOW-VOL; "
        ">= median = HIGH-VOL. Rebalance bar every 6th 4H bar."
    )
    emit(f"Discovery/validation split cutoff: `{cutoff_ts.strftime('%Y-%m-%d %H:%M UTC')}`")
    emit("")
    emit("### Discovery (first ~70%)")
    emit("")
    emit("| Symbol | Rebalance bars | LOW-VOL | HIGH-VOL | Meets >=80? |")
    emit("|--------|----------------|---------|----------|-------------|")
    for r in regime_rows:
        ok = "YES" if r["d_total"] >= MIN_DISCOVERY_OBS else "NO"
        emit(f"| {r['sym']} | {r['d_total']} | {r['d_low']} | {r['d_high']} | {ok} |")
    emit("")
    d_pooled = sum(r["d_total"] for r in regime_rows)
    d_pooled_low = sum(r["d_low"] for r in regime_rows)
    d_pooled_high = sum(r["d_high"] for r in regime_rows)
    emit(f"**Pooled discovery**: {d_pooled} rebalance obs ({d_pooled_low} LOW-VOL, {d_pooled_high} HIGH-VOL)")
    emit("")
    emit("### Validation (last ~30%)")
    emit("")
    emit("| Symbol | Rebalance bars | LOW-VOL | HIGH-VOL | Meets >=40? |")
    emit("|--------|----------------|---------|----------|-------------|")
    for r in regime_rows:
        ok = "YES" if r["v_total"] >= MIN_VALIDATION_OBS else "NO"
        emit(f"| {r['sym']} | {r['v_total']} | {r['v_low']} | {r['v_high']} | {ok} |")
    emit("")
    v_pooled = sum(r["v_total"] for r in regime_rows)
    v_pooled_low = sum(r["v_low"] for r in regime_rows)
    v_pooled_high = sum(r["v_high"] for r in regime_rows)
    emit(f"**Pooled validation**: {v_pooled} rebalance obs ({v_pooled_low} LOW-VOL, {v_pooled_high} HIGH-VOL)")
    emit("")
    emit("## ZEC liquidity check")
    emit("")
    if zec_liq:
        emit(f"- Avg daily quote volume (USD): **{zec_liq['avg_daily_qvol_usd']:,.0f}**")
        emit(
            f"- Avg 4H H/L range proxy: **{zec_liq['avg_hl_spread_pct']:.4f}%** "
            f"(this is intrabar price RANGE, not bid-ask spread)"
        )
        emit(f"- Volume minimum threshold: ${ZEC_MIN_AVG_DAILY_QVOL_USD:,}/day")
        emit(f"- Extreme-volatility flag (H/L range > {ZEC_HL_RANGE_EXTREME_PCT}%): "
             f"{'YES' if zec_extreme_volatility else 'NO'}")
        emit("")
        if zec_include and not zec_extreme_volatility:
            emit(
                "**Recommendation: INCLUDE ZEC.** Volume well above threshold ($500k/day). "
                "H/L range is normal for a mid-cap perp. "
                "Bid-ask spread not directly measurable from OHLCV; the 8 bps one-way assumption "
                "is standard and should be flagged as an assumption, not confirmed."
            )
        elif zec_include and zec_extreme_volatility:
            emit(
                "**Recommendation: INCLUDE ZEC with volatility caveat.** Volume adequate but "
                f"H/L range ({zec_liq['avg_hl_spread_pct']:.2f}%) is extreme. "
                "Intrabar moves may produce worse fill prices than assumed. Flag in pre-registration."
            )
        else:
            emit(
                "**Recommendation: EXCLUDE ZEC.** Avg daily volume below $500k/day threshold — "
                "liquidity too thin for reliable fill assumption at 8 bps one-way cost."
            )
    emit("")
    emit("## Notes for pre-registration lock")
    emit("")
    emit(
        f"1. Exact discovery/validation cutoff date: owner sets from the estimate above "
        f"(`{cutoff_ts.strftime('%Y-%m-%dT%H:%M:%SZ')}`)."
    )
    emit("2. Dataset SHA-256: record combined hash above at lock.")
    emit("3. ZEC include/exclude: see recommendation above.")
    emit("4. Baseline seed: owner fixes integer seed (§2.4).")
    emit("")

    report_text = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(f"Report written: {REPORT_PATH}")
    print(f"Verdict: {verdict}")


if __name__ == "__main__":
    main()
