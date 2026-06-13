"""Setup I data acquisition: download BTC/ETH aggTrades and aggregate to hourly.

Uses streaming download to temp files + row-by-row ZIP decompression to handle
peak monthly files (~1.3 GB compressed / ~13 GB decompressed) without loading
the full decompressed content into RAM.

Peak disk usage during acquisition: one monthly zip at a time (~1.3 GB max).
Peak RAM: ~200 MB (hourly-bin dict for both symbols).
Stored output: hourly CSVs, ~10 MB total.

Run from project root:
    python -m research.signal_observation._acquire_setup_i
"""
from __future__ import annotations

import csv
import io
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "research" / "signal_observation" / "data" / "setup_i"

sys.path.insert(0, str(ROOT))

from research.signal_observation.aggtrades_downloader import (
    HOURLY_HEADER,
    HourBin,
    daily_url,
    detect_ts_unit,
    monthly_url,
)

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
# Earliest non-404: 2020-01 confirmed via HEAD. 2019-09 and 2019-10 return 404.
START_DATE = date(2020, 1, 1)

# Compressed download size estimates from HEAD-request sampling (June 2026):
#   BTC: 2020-01=97.8 MB, 2020-06=163.2 MB, 2021-03=787.1 MB,
#        2021-06=1325.2 MB, 2022-03=597.2 MB, 2023-01=370.5 MB,
#        2024-06=324.3 MB, 2025-01=660.3 MB  → ~32 GB total
#   ETH: 2020-01=23.7 MB, 2020-06=73.4 MB, 2021-06=833.1 MB,
#        2022-03=381.0 MB, 2023-01=333.3 MB, 2024-06=353.9 MB,
#        2025-01=697.5 MB  → ~23 GB total
_EST_SIZES_GB = {"BTCUSDT": 32, "ETHUSDT": 23}

_NCOLS_MIN = 7
# Per-file connect/read timeout (seconds). urllib applies this per network read
# operation, not total transfer, so large files still complete with 300 s here.
_TIMEOUT_S = 300


# ---------------------------------------------------------------------------
# Streaming zip processor
# ---------------------------------------------------------------------------

def _process_zip(tmp_path: Path, bins: dict[int, HourBin]) -> int:
    """Parse a local aggTrades zip row-by-row and fold rows into hourly bins.

    Returns the number of trade rows processed.
    Never loads the full decompressed CSV into memory.
    """
    with zipfile.ZipFile(tmp_path) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(f"zip has no .csv entry: {zf.namelist()!r}")

        unit: str | None = None
        row_count = 0

        with zf.open(csv_names[0]) as raw_stream:
            for line in csv.reader(io.TextIOWrapper(raw_stream, encoding="utf-8")):
                if not line or not line[0].strip():
                    continue
                first = line[0].strip().lstrip("-")
                if not first.isdigit():
                    continue  # header row
                if len(line) < _NCOLS_MIN:
                    raise ValueError(
                        f"aggTrades row has {len(line)} cols (need {_NCOLS_MIN}): {line!r}"
                    )
                try:
                    ts_int = int(line[5])
                    price = Decimal(line[1])
                    qty = Decimal(line[2])
                    ibm_raw = line[6].strip().lower()
                    if ibm_raw == "true":
                        is_buyer_maker = True
                    elif ibm_raw == "false":
                        is_buyer_maker = False
                    else:
                        raise ValueError(f"invalid isBuyerMaker: {line[6]!r}")
                except (InvalidOperation, ValueError) as exc:
                    raise ValueError(f"invalid row {line!r}: {exc}") from exc

                if unit is None:
                    unit = detect_ts_unit(ts_int)

                ms = ts_int // 1000 if unit == "us" else ts_int
                hour_ms = (ms // 3_600_000) * 3_600_000

                if hour_ms not in bins:
                    bins[hour_ms] = HourBin(open=price, high=price, low=price, close=price)
                b = bins[hour_ms]
                if price > b.high:
                    b.high = price
                if price < b.low:
                    b.low = price
                b.close = price
                if is_buyer_maker:
                    b.taker_sell_vol += qty
                else:
                    b.taker_buy_vol += qty

                row_count += 1

    return row_count


# ---------------------------------------------------------------------------
# Streaming download
# ---------------------------------------------------------------------------

def _download_to_temp(url: str, tmp_dir: Path) -> tuple[Path | None, int]:
    """Stream-download url to a named temp file in tmp_dir.

    Returns (path, bytes_on_disk) or (None, 0) on 404.
    Raises on any non-404 HTTP error.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            with tempfile.NamedTemporaryFile(
                suffix=".zip", dir=tmp_dir, delete=False
            ) as tmp:
                tmp_path = Path(tmp.name)
                shutil.copyfileobj(resp, tmp, length=1 << 20)  # 1 MB chunks
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, 0
        raise

    return tmp_path, tmp_path.stat().st_size


# ---------------------------------------------------------------------------
# Per-symbol acquisition
# ---------------------------------------------------------------------------

def acquire_symbol(
    symbol: str,
    start_date: date,
    end_date: date,
) -> dict:
    """Download all monthly (plus current-month daily) zips for one symbol.

    Streams each zip through _process_zip, deletes the temp zip immediately
    after, so peak disk usage is one monthly file at a time.

    Returns dict with keys: bins, total_bytes_downloaded.
    """
    bins: dict[int, HourBin] = {}
    total_bytes_downloaded = 0
    today = date.today()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path_dir = Path(tmp_dir)

        year, month = start_date.year, start_date.month
        while (year, month) <= (end_date.year, end_date.month):
            is_current = year == today.year and month == today.month

            if not is_current:
                url = monthly_url(symbol, year, month)
                sys.stdout.write(f"  {year}-{month:02d} ")
                sys.stdout.flush()

                zip_path, dl_bytes = _download_to_temp(url, tmp_path_dir)
                if zip_path is None:
                    sys.stdout.write("404\n")
                else:
                    total_bytes_downloaded += dl_bytes
                    _process_zip(zip_path, bins)
                    zip_path.unlink()
                    sys.stdout.write(f"{dl_bytes / 1e6:.1f} MB\n")
            else:
                d = date(year, month, 1)
                while d <= end_date and d.month == month:
                    url = daily_url(symbol, year, month, d.day)
                    zip_path, dl_bytes = _download_to_temp(url, tmp_path_dir)
                    if zip_path is not None:
                        total_bytes_downloaded += dl_bytes
                        _process_zip(zip_path, bins)
                        zip_path.unlink()
                    d += timedelta(days=1)
                sys.stdout.write(
                    f"  {year}-{month:02d} (daily) done\n"
                )

            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1

    return {"bins": bins, "total_bytes_downloaded": total_bytes_downloaded}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Setup I — aggTrades Acquisition ===")
    print()
    total_est_gb = sum(_EST_SIZES_GB.values())
    print(f"Estimated compressed download (HEAD-sampled June 2026):")
    for sym, gb in _EST_SIZES_GB.items():
        print(f"  {sym}: ~{gb} GB")
    print(f"  Combined: ~{total_est_gb} GB")
    print(f"Estimated stored (hourly CSVs, 2 symbols): ~10 MB")
    print()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    end_date = date.today() - timedelta(days=1)

    report_lines: list[str] = []

    for symbol in SYMBOLS:
        print(f"--- {symbol} (est. ~{_EST_SIZES_GB[symbol]} GB download) ---")
        try:
            result = acquire_symbol(symbol, START_DATE, end_date)
        except Exception as exc:
            msg = f"ERROR in {symbol}: {type(exc).__name__}: {exc}"
            print(f"\n{msg}", file=sys.stderr)
            sys.exit(1)

        bins = result["bins"]
        total_dl = result["total_bytes_downloaded"]

        output_path = DATA_DIR / f"{symbol}_aggtrades_1h.csv"
        sorted_hours = sorted(bins)
        with output_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(HOURLY_HEADER)
            for hour_ms in sorted_hours:
                b = bins[hour_ms]
                dt = datetime.fromtimestamp(hour_ms / 1000, tz=UTC)
                writer.writerow([
                    dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    str(b.open),
                    str(b.high),
                    str(b.low),
                    str(b.close),
                    str(b.taker_buy_vol),
                    str(b.taker_sell_vol),
                ])

        stored_bytes = output_path.stat().st_size

        if sorted_hours:
            first_dt = datetime.fromtimestamp(sorted_hours[0] / 1000, tz=UTC)
            last_dt = datetime.fromtimestamp(sorted_hours[-1] / 1000, tz=UTC)
            coverage = (
                f"{first_dt.strftime('%Y-%m-%d')} .. {last_dt.strftime('%Y-%m-%d')}"
            )
        else:
            coverage = "NO DATA"

        line = (
            f"{symbol}: coverage={coverage}  hours={len(sorted_hours)}"
            f"  downloaded={total_dl / 1e9:.2f} GB"
            f"  stored={stored_bytes / 1e6:.2f} MB"
        )
        report_lines.append(line)
        print(f"\n  {line}\n")

    print("=== Acquisition complete ===")
    for ln in report_lines:
        print(ln)


if __name__ == "__main__":
    main()
