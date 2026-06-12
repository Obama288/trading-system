"""Setup E Stage 1 feasibility script: data quality + episode counting only.

HARD RULE (constitution §1, Stage 1): this script computes NO outcome metrics.
No returns, win rates, expectancy, MFE/MAE, or any value derived from prices
AFTER a signal bar. Violation taints the discovery window.

What this script does (all allowed at Stage 1):
  - Quality assessment of each downloaded OHLCV and liquidation CSV pair
  - Counting potential cascade episodes per the pre-registration signal
    definition (contemporaneous signal identification, no look-ahead)
  - Reporting bar coverage, gap fraction, episode counts per symbol

Output: data/setup_e/feasibility_report.json

Usage:
    python -m research.signal_observation.run_setup_e_feasibility [--data-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path


# ---------------------------------------------------------------------------
# Liquidation CSV loader
# ---------------------------------------------------------------------------

_LIQ_REQUIRED = ("timestamp_utc", "long_notional_usd", "short_notional_usd")


def _load_liquidation_csv(path: Path) -> list[dict]:
    """Load liquidation CSV into list of {timestamp, long, short} dicts.

    Timestamps are returned as datetime objects (UTC). Notional values are
    Decimal. No price-after-signal computation is performed here.
    """
    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty CSV")
        headers = tuple(h.strip().lower() for h in reader.fieldnames)
        for col in _LIQ_REQUIRED:
            if col not in headers:
                raise ValueError(f"{path}: missing column '{col}'")
        for i, row in enumerate(reader, start=2):
            ts_str = (row.get("timestamp_utc") or "").strip()
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"{path}: row {i}: bad timestamp: {ts_str!r}") from exc
            rows.append(
                {
                    "timestamp": ts,
                    "long": Decimal(str(row["long_notional_usd"])),
                    "short": Decimal(str(row["short_notional_usd"])),
                }
            )
    rows.sort(key=lambda r: r["timestamp"])
    return rows


# ---------------------------------------------------------------------------
# Episode counting — no outcome metrics
# ---------------------------------------------------------------------------

_BARS_PER_DAY_4H = 6
_TRAILING_DAYS = 30
_TRAILING_BARS = _BARS_PER_DAY_4H * _TRAILING_DAYS  # 180 bars

_CASCADE_PERCENTILE = 95  # pre-registration §2.3
_EXHAUSTION_THRESHOLD_PCT = 50  # median = 50th percentile


def _percentile(values: list[Decimal], pct: int) -> Decimal:
    """Simple nearest-rank percentile (no interpolation)."""
    if not values:
        return Decimal("0")
    s = sorted(values)
    rank = max(0, int(len(s) * pct / 100) - 1)
    return s[rank]


def count_cascade_episodes(
    ohlcv: list[dict],
    liq: list[dict],
) -> dict:
    """Count potential cascade episodes — NO outcome computation.

    Signal definition from SETUP_E_PREREGISTRATION.md §2.3:
      - Cascade bar: long-liq > 95th percentile of trailing 30-day (180-bar)
        long-liq distribution AND bar close < bar open (down bar)
      - Signal/exhaustion bar: first subsequent bar where long-liq falls below
        the trailing 30-day median
      - One episode per cascade; non-overlapping (new cascade cannot start
        while a prior episode is unresolved)

    Returns dict with episode count and metadata. No return values, no prices
    after the signal bar are read or stored.
    """
    # Align by timestamp (both sorted ascending)
    ts_to_ohlcv = {c["timestamp"]: c for c in ohlcv}
    ts_to_liq = {r["timestamp"]: r for r in liq}

    # Intersection of timestamps
    common_ts = sorted(ts_to_ohlcv.keys() & ts_to_liq.keys())
    if not common_ts:
        return {"episodes": 0, "cascade_bars": 0, "aligned_bars": 0}

    aligned = [
        {"ts": ts, **ts_to_ohlcv[ts], **ts_to_liq[ts]} for ts in common_ts
    ]
    n = len(aligned)

    # --- Pass 1: identify cascade bars ---
    cascade_bars: list[int] = []
    for i in range(_TRAILING_BARS, n):
        window_longs = [aligned[j]["long"] for j in range(i - _TRAILING_BARS, i)]
        threshold_95 = _percentile(window_longs, _CASCADE_PERCENTILE)
        bar = aligned[i]
        # Cascade: long-liq burst AND down bar
        if bar["long"] > threshold_95 and bar["close"] < bar["open"]:
            cascade_bars.append(i)

    # --- Pass 2: find exhaustion bars, count non-overlapping episodes ---
    episodes = 0
    next_allowed = 0  # no new episode may start before this index
    for ci in cascade_bars:
        if ci < next_allowed:
            continue  # inside a prior episode's influence window
        # Look forward for the first bar where long-liq falls below trailing median
        for j in range(ci + 1, min(ci + 25, n)):  # look-ahead window capped
            window_longs = [
                aligned[k]["long"]
                for k in range(max(0, j - _TRAILING_BARS), j)
            ]
            median = _percentile(window_longs, _EXHAUSTION_THRESHOLD_PCT)
            if aligned[j]["long"] < median:
                episodes += 1
                next_allowed = j + 1  # constitution §3.8: no overlap
                break

    return {
        "episodes": episodes,
        "cascade_bars": len(cascade_bars),
        "aligned_bars": n,
        "first_bar": common_ts[0].isoformat() if common_ts else None,
        "last_bar": common_ts[-1].isoformat() if common_ts else None,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _find_symbol_pairs(data_dir: Path) -> list[tuple[str, Path, Path]]:
    """Find (symbol_id, ohlcv_path, liq_path) pairs from data directory."""
    pairs = []
    for ohlcv_path in sorted(data_dir.glob("*_ohlcv_4h.csv")):
        stem = ohlcv_path.name[: -len("_ohlcv_4h.csv")]
        liq_path = data_dir / f"{stem}_liquidation_4h.csv"
        if liq_path.exists():
            pairs.append((stem, ohlcv_path, liq_path))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Setup E Stage 1 feasibility: quality check + episode count. "
            "NO outcome metrics computed (constitution §1)."
        )
    )
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).parent / "data" / "setup_e"),
        help="Directory containing *_ohlcv_4h.csv and *_liquidation_4h.csv files",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"ERROR: data directory not found: {data_dir}", file=sys.stderr)
        print("Run TASK 2 acquisition first.", file=sys.stderr)
        return 2

    pairs = _find_symbol_pairs(data_dir)
    if not pairs:
        print(f"No symbol pairs found in {data_dir}", file=sys.stderr)
        return 2

    # Deferred import to keep startup visible
    from research.signal_observation.csv_loader import load_ohlcv_csv
    from research.simcore.quality import assess_candles, passes, to_json_dict

    symbol_reports = []
    total_episodes = 0
    quality_passes = 0
    quality_fails = 0

    for stem, ohlcv_path, liq_path in pairs:
        # --- OHLCV quality ---
        ohlcv_candles = load_ohlcv_csv(ohlcv_path)
        ohlcv_dict = [
            {
                "timestamp": c.timestamp,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in ohlcv_candles
        ]
        q_report = assess_candles(ohlcv_candles)
        ok, reasons = passes(q_report)
        if ok:
            quality_passes += 1
        else:
            quality_fails += 1

        # --- Liquidation data ---
        liq_rows = _load_liquidation_csv(liq_path)

        # --- Episode count (NO outcome metrics) ---
        epi = count_cascade_episodes(ohlcv_dict, liq_rows)
        total_episodes += epi["episodes"]

        sym_report = {
            "symbol": stem,
            "ohlcv_bars": q_report.total_bars,
            "ohlcv_quality_pass": ok,
            "ohlcv_quality_reasons": reasons,
            "ohlcv_missing_fraction": str(q_report.missing_fraction),
            "first_bar": epi.get("first_bar"),
            "last_bar": epi.get("last_bar"),
            "aligned_bars": epi["aligned_bars"],
            "cascade_bars_detected": epi["cascade_bars"],
            "signal_episodes": epi["episodes"],
        }
        symbol_reports.append(sym_report)
        print(
            f"{stem}: {q_report.total_bars} bars "
            f"({'PASS' if ok else 'FAIL'}) "
            f"episodes={epi['episodes']}"
        )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "data_dir": str(data_dir),
        "symbols_processed": len(symbol_reports),
        "quality_passes": quality_passes,
        "quality_fails": quality_fails,
        "total_signal_episodes": total_episodes,
        "minimum_required_discovery": 80,
        "minimum_required_validation": 40,
        "episode_count_vs_minimum": (
            "SUFFICIENT" if total_episodes >= 80 else "INSUFFICIENT — owner decision required per §2.6"
        ),
        "note": (
            "HARD RULE: no outcome metrics in this report. "
            "Episode counts are signal identification only (contemporaneous). "
            "Forward returns are NOT computed here (constitution Stage 1)."
        ),
        "symbols": symbol_reports,
    }

    out_path = data_dir / "feasibility_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nTotal episodes: {total_episodes} (minimum: 80)")
    print(f"Quality: {quality_passes} pass / {quality_fails} fail")
    print(f"Report: {out_path}")
    return 0 if quality_fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
