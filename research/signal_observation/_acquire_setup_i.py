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
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "research" / "signal_observation" / "data" / "setup_i"

sys.path.insert(0, str(ROOT))

from research.signal_observation.aggtrades_downloader import (
    HOURLY_HEADER,
    daily_url,
    detect_ts_unit,
    monthly_url,
)

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
# Earliest non-404: 2020-01 confirmed via HEAD. 2019-09 and 2019-10 return 404.
START_DATE = date(2024, 1, 1)

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

def _process_zip(tmp_path: Path, bins: dict[int, list[float]]) -> int:
    """Parse a local aggTrades zip row-by-row and fold rows into hourly bins.

    bins entries: [open, high, low, close, taker_buy_vol, taker_sell_vol] as float.
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
                    price = float(line[1])
                    qty = float(line[2])
                    ibm_raw = line[6].strip().lower()
                    if ibm_raw == "true":
                        is_buyer_maker = True
                    elif ibm_raw == "false":
                        is_buyer_maker = False
                    else:
                        raise ValueError(f"invalid isBuyerMaker: {line[6]!r}")
                except ValueError as exc:
                    raise ValueError(f"invalid row {line!r}: {exc}") from exc

                if unit is None:
                    unit = detect_ts_unit(ts_int)

                ms = ts_int // 1000 if unit == "us" else ts_int
                hour_ms = (ms // 3_600_000) * 3_600_000

                if hour_ms not in bins:
                    # [open, high, low, close, taker_buy_vol, taker_sell_vol]
                    bins[hour_ms] = [price, price, price, price, 0.0, 0.0]
                b = bins[hour_ms]
                if price > b[1]:
                    b[1] = price
                if price < b[2]:
                    b[2] = price
                b[3] = price
                if is_buyer_maker:
                    b[5] += qty  # buyer is maker → taker is SELLER → taker_sell_vol
                else:
                    b[4] += qty  # buyer is taker → taker_buy_vol

                row_count += 1

    return row_count


# ---------------------------------------------------------------------------
# Resume helpers
# ---------------------------------------------------------------------------

def _load_existing_bins(
    csv_path: Path,
) -> tuple[dict[int, list[float]], set[tuple[int, int]]]:
    """Read an existing hourly CSV and return (bins, done_months).

    Any month present in the CSV was written by a completed run, so it is safe
    to skip re-downloading.
    """
    bins: dict[int, list[float]] = {}
    done_months: set[tuple[int, int]] = set()
    if not csv_path.exists():
        return bins, done_months
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp_utc"]  # "2024-01-01T00:00:00Z"
            dt = datetime(
                int(ts[0:4]), int(ts[5:7]), int(ts[8:10]),
                int(ts[11:13]), int(ts[14:16]), int(ts[17:19]),
                tzinfo=UTC,
            )
            hour_ms = int(dt.timestamp() * 1000)
            bins[hour_ms] = [
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row["taker_buy_vol"]),
                float(row["taker_sell_vol"]),
            ]
            done_months.add((dt.year, dt.month))
    return bins, done_months


# ---------------------------------------------------------------------------
# Flow-direction sanity guard
# ---------------------------------------------------------------------------

def _assert_flow_direction(bins: dict[int, list[float]], symbol: str) -> None:
    """Guard against is_buyer_maker column inversion.

    In hours where price rose strongly (close > open by ≥ 0.2%), net aggressive
    buying should dominate: mean(taker_buy_vol − taker_sell_vol) > 0.
    A negative mean is the exact signature of a taker_buy/taker_sell swap in
    _process_zip. Requires ≥ 50 qualifying bars; silent below that threshold.
    """
    up_bars = [
        b for b in bins.values()
        if b[0] > 0 and b[3] > b[0] * 1.002 and (b[4] + b[5]) > 0
    ]
    if len(up_bars) < 50:
        return
    mean_flow = sum(b[4] - b[5] for b in up_bars) / len(up_bars)
    if mean_flow <= 0:
        raise ValueError(
            f"{symbol}: flow-direction sanity FAIL — "
            f"mean(taker_buy − taker_sell) = {mean_flow:.6f} across {len(up_bars)} "
            f"strong-up-move hours is ≤ 0. "
            f"Inversion signature detected: check _process_zip is_buyer_maker assignment."
        )


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
    out_path = DATA_DIR / f"{symbol}_aggtrades_1h.csv"
    bins, done_months = _load_existing_bins(out_path)
    total_bytes_downloaded = 0
    today = date.today()

    # Count total months in range for progress display.
    total_months = 0
    _y, _m = start_date.year, start_date.month
    while (_y, _m) <= (end_date.year, end_date.month):
        total_months += 1
        _m = _m % 12 + 1
        if _m == 1:
            _y += 1

    if done_months:
        skipped = sorted(done_months)
        print(
            f"  Resume: {len(skipped)} months already in CSV"
            f" ({skipped[0][0]}-{skipped[0][1]:02d}.."
            f"{skipped[-1][0]}-{skipped[-1][1]:02d})"
        )

    month_num = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path_dir = Path(tmp_dir)

        year, month = start_date.year, start_date.month
        while (year, month) <= (end_date.year, end_date.month):
            month_num += 1
            is_current = year == today.year and month == today.month

            if (year, month) in done_months:
                next_y = year + 1 if month == 12 else year
                next_m = 1 if month == 12 else month + 1
                lo = int(datetime(year, month, 1, tzinfo=UTC).timestamp() * 1000)
                hi = int(datetime(next_y, next_m, 1, tzinfo=UTC).timestamp() * 1000)
                n_bins = sum(1 for h in bins if lo <= h < hi)
                print(
                    f"  {symbol} {year}-{month:02d} skip"
                    f"  {n_bins} bins  [{month_num}/{total_months}]"
                )
            elif not is_current:
                url = monthly_url(symbol, year, month)
                sys.stdout.write(
                    f"  {symbol} {year}-{month:02d} downloading... "
                )
                sys.stdout.flush()

                zip_path, dl_bytes = _download_to_temp(url, tmp_path_dir)
                if zip_path is None:
                    sys.stdout.write(f"404  [{month_num}/{total_months}]\n")
                else:
                    total_bytes_downloaded += dl_bytes
                    bins_before = len(bins)
                    _process_zip(zip_path, bins)
                    zip_path.unlink()
                    n_new = len(bins) - bins_before
                    sys.stdout.write(
                        f"done  {n_new} bins  {dl_bytes / 1e6:.1f} MB"
                        f"  [{month_num}/{total_months}]\n"
                    )
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
                    f"  {symbol} {year}-{month:02d} (daily) done"
                    f"  [{month_num}/{total_months}]\n"
                )

            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1

    _assert_flow_direction(bins, symbol)
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
    end_date = date(2026, 5, 31)

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
                b = bins[hour_ms]  # [open, high, low, close, taker_buy, taker_sell]
                dt = datetime.fromtimestamp(hour_ms / 1000, tz=UTC)
                writer.writerow([
                    dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    repr(b[0]),
                    repr(b[1]),
                    repr(b[2]),
                    repr(b[3]),
                    repr(b[4]),
                    repr(b[5]),
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
