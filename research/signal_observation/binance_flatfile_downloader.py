"""Binance data.binance.vision flat-file kline downloader for Setup H.

Downloads monthly + daily zip archives from data.binance.vision (no API key,
no auth) for USD-M USDT-perpetual contracts. Output CSV matches the project
standard format (timestamp, open, high, low, close, volume) so load_ohlcv_csv
works unchanged.

URL conventions verified against binance-public-data repo:
  data/futures/um/{monthly|daily}/klines/{SYMBOL}/{INTERVAL}/
      {SYMBOL}-{INTERVAL}-{YYYY}-{MM}.zip          (monthly)
      {SYMBOL}-{INTERVAL}-{YYYY}-{MM}-{DD}.zip     (daily)
404 = symbol/date not yet available; skipped silently.
"""
from __future__ import annotations

import csv
import io
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

_BASE_URL = "https://data.binance.vision/data/futures/um"
_MONTHLY_URL = (
    "{base}/monthly/klines/{symbol}/{interval}/"
    "{symbol}-{interval}-{year}-{month:02d}.zip"
)
_DAILY_URL = (
    "{base}/daily/klines/{symbol}/{interval}/"
    "{symbol}-{interval}-{year}-{month:02d}-{day:02d}.zip"
)

CSV_HEADER = ("timestamp", "open", "high", "low", "close", "volume")
SUPPORTED_INTERVALS = (
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h", "1d",
)
_NCOLS = 12  # flat-file CSV has 12 columns, no header row


def monthly_url(symbol: str, interval: str, year: int, month: int) -> str:
    """Return the data.binance.vision URL for a monthly klines zip."""
    return _MONTHLY_URL.format(
        base=_BASE_URL, symbol=symbol, interval=interval,
        year=year, month=month,
    )


def daily_url(symbol: str, interval: str, year: int, month: int, day: int) -> str:
    """Return the data.binance.vision URL for a daily klines zip."""
    return _DAILY_URL.format(
        base=_BASE_URL, symbol=symbol, interval=interval,
        year=year, month=month, day=day,
    )


def download_flatfile_klines(
    *,
    symbol: str,
    interval: str,
    output_csv: Path | str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Path:
    """Download USD-M perp klines from data.binance.vision flat files.

    Uses monthly zips for complete elapsed months, daily zips for the current
    (incomplete) month. 404s are silently skipped — the symbol's actual start
    date is discovered empirically. Returns the path of the written output CSV.
    """
    if not symbol:
        raise ValueError("symbol must not be empty")
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"interval must be one of: {SUPPORTED_INTERVALS}")

    today = date.today()
    if end_date is None:
        end_date = today - timedelta(days=1)
    if start_date is None:
        start_date = date(2019, 9, 1)

    rows: dict[int, tuple[str, str, str, str, str, str]] = {}

    year, month = start_date.year, start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        is_current_month = (year == today.year and month == today.month)
        if not is_current_month:
            url = monthly_url(symbol, interval, year, month)
            batch = _download_zip(url)
            if batch is not None:
                _merge_rows(batch, rows, start_date, end_date)
        else:
            d = date(year, month, 1)
            while d <= end_date and d.month == month:
                url = daily_url(symbol, interval, year, month, d.day)
                batch = _download_zip(url)
                if batch is not None:
                    _merge_rows(batch, rows, start_date, end_date)
                d += timedelta(days=1)

        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_rows = [rows[k] for k in sorted(rows)]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)
        writer.writerows(sorted_rows)
    return output_path


def parse_zip_csv(data: bytes) -> list[list[str]]:
    """Extract kline rows from a data.binance.vision zip archive.

    The zip contains exactly one CSV with no header row; _NCOLS columns per row.
    Exported as a module-level function so tests can call it directly.
    """
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(
                f"zip contains no .csv file; entries: {zf.namelist()!r}"
            )
        raw = zf.read(csv_names[0]).decode("utf-8")

    rows: list[list[str]] = []
    for line in csv.reader(io.StringIO(raw)):
        if not line or not line[0].strip():
            continue
        if len(line) < _NCOLS:
            raise ValueError(
                f"kline row has {len(line)} columns, expected >= {_NCOLS}"
            )
        rows.append(line)
    return rows


def _download_zip(url: str) -> list[list[str]] | None:
    """Fetch a zip archive. Returns parsed rows or None on 404."""
    req = urllib.request.Request(url, headers={"User-Agent": "research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    return parse_zip_csv(data)


def _merge_rows(
    raw_rows: list[list[str]],
    target: dict[int, tuple[str, str, str, str, str, str]],
    start_date: date,
    end_date: date,
) -> None:
    start_ms = int(
        datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)
        .timestamp() * 1000
    )
    end_ms = int(
        (datetime(end_date.year, end_date.month, end_date.day, tzinfo=UTC)
         + timedelta(days=1)).timestamp() * 1000
    )
    for row in raw_rows:
        open_ms = int(row[0])
        if open_ms < start_ms or open_ms >= end_ms:
            continue
        try:
            parsed: tuple[str, str, str, str, str, str] = (
                _ms_to_iso(open_ms),
                str(Decimal(row[1])),
                str(Decimal(row[2])),
                str(Decimal(row[3])),
                str(Decimal(row[4])),
                str(Decimal(row[5])),
            )
        except (InvalidOperation, IndexError, ValueError) as exc:
            raise ValueError(f"invalid kline row {row!r}: {exc}") from exc
        target[open_ms] = parsed


def _ms_to_iso(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000, tz=UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
