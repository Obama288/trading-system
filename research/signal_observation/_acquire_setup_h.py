"""Setup H data acquisition: download 4H klines for 9 alt perp symbols.

Writes to research/signal_observation/data/setup_h/{SYMBOL}_4h.csv.
ZEC also gets avg daily quote volume and spread proxy metrics.
Run from project root:
    python -m research.signal_observation._acquire_setup_h
"""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime, UTC
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "research" / "signal_observation" / "data" / "setup_h"

sys.path.insert(0, str(ROOT))

from research.signal_observation.binance_flatfile_downloader import download_flatfile_klines
from research.signal_observation.csv_loader import load_ohlcv_csv
from research.simcore.quality import assess_candles, passes, to_json_dict

SYMBOLS = [
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "ZECUSDT",
]

START_DATE = date(2019, 9, 1)


def _coverage_summary(candles) -> str:
    if not candles:
        return "NO DATA"
    first = candles[0].timestamp.strftime("%Y-%m-%d")
    last = candles[-1].timestamp.strftime("%Y-%m-%d")
    return f"{first} .. {last} ({len(candles)} bars)"


def _zec_metrics(candles) -> dict:
    """Avg daily quote volume and spread proxy for ZEC liquidity check."""
    if len(candles) < 6:
        return {"avg_daily_quote_vol": None, "avg_hl_spread_pct": None}

    days: dict[str, list] = {}
    for c in candles:
        d = c.timestamp.strftime("%Y-%m-%d")
        days.setdefault(d, []).append(c)

    daily_qvols = []
    for day_candles in days.values():
        total = sum(c.volume * c.close for c in day_candles)
        daily_qvols.append(float(total))
    avg_qvol = sum(daily_qvols) / len(daily_qvols) if daily_qvols else 0.0

    hl_spreads = []
    for c in candles:
        if c.low > 0:
            spread = float((c.high - c.low) / c.close * 100)
            hl_spreads.append(spread)
    avg_spread = sum(hl_spreads) / len(hl_spreads) if hl_spreads else 0.0

    return {
        "avg_daily_quote_vol_usd": round(avg_qvol, 0),
        "avg_hl_spread_pct": round(avg_spread, 4),
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    end_date = date.today()
    report_lines = []

    for symbol in SYMBOLS:
        out_path = DATA_DIR / f"{symbol}_4h.csv"
        sys.stdout.write(f"Downloading {symbol} ... ")
        sys.stdout.flush()
        try:
            download_flatfile_klines(
                symbol=symbol,
                interval="4h",
                output_csv=out_path,
                start_date=START_DATE,
                end_date=end_date,
            )
            sys.stdout.write("done\n")
        except Exception as e:
            sys.stdout.write(f"FAILED: {e}\n")
            report_lines.append(f"{symbol}: DOWNLOAD ERROR - {e}")
            continue

        candles = load_ohlcv_csv(out_path)
        report = assess_candles(candles)
        ok, reasons = passes(report)
        coverage = _coverage_summary(candles)
        status = "PASS" if ok else f"FAIL({'; '.join(reasons)})"

        line = f"{symbol}: {coverage}  quality={status}"
        if symbol == "ZECUSDT":
            metrics = _zec_metrics(candles)
            line += (
                f"  ZEC_avg_daily_qvol_usd={metrics['avg_daily_quote_vol_usd']}"
                f"  ZEC_avg_hl_spread_pct={metrics['avg_hl_spread_pct']}"
            )
        report_lines.append(line)
        sys.stdout.write(f"  {line}\n")

    print("\n--- Coverage report ---")
    for ln in report_lines:
        print(ln)


if __name__ == "__main__":
    main()
