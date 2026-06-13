"""Binance USD-M perp aggTrades hourly aggregator for Setup I.

Downloads monthly/daily aggTrades zip archives from data.binance.vision,
aggregates to 1-hour OHLCV + signed-flow bins on the fly, and writes the
hourly series to a local CSV. Raw ticks are never persisted to disk.

URL schema (verified against binance-public-data GitHub repo):
  data/futures/um/monthly/aggTrades/{SYM}/{SYM}-aggTrades-{YYYY}-{MM}.zip
  data/futures/um/daily/aggTrades/{SYM}/{SYM}-aggTrades-{YYYY}-{MM}-{DD}.zip

CSV schema — UM futures aggTrades (7 cols, no isBestMatch column):
  col 0: agg_trade_id
  col 1: price
  col 2: qty
  col 3: first_trade_id
  col 4: last_trade_id
  col 5: transact_time  (milliseconds or microseconds — detected per file)
  col 6: is_buyer_maker (True/False string)
  [col 7+: ignored; present in some spot zips but absent in UM futures]

Timestamp unit detection:
  Binance switched some UM futures series to microseconds starting 2025.
  Any transact_time >= 10^15 is treated as microseconds; below is milliseconds.
  Detection is performed once per zip from the first data row.

isBuyerMaker semantics:
  isBuyerMaker=False  → aggressor is a BUYER  (taker-buy volume)
  isBuyerMaker=True   → aggressor is a SELLER (taker-sell volume)

Output CSV (one row per UTC hour):
  timestamp_utc, open, high, low, close, taker_buy_vol, taker_sell_vol
"""
from __future__ import annotations

import csv
import io
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

_BASE_URL = "https://data.binance.vision/data/futures/um"
_MONTHLY_URL = (
    "{base}/monthly/aggTrades/{symbol}/"
    "{symbol}-aggTrades-{year}-{month:02d}.zip"
)
_DAILY_URL = (
    "{base}/daily/aggTrades/{symbol}/"
    "{symbol}-aggTrades-{year}-{month:02d}-{day:02d}.zip"
)

_NCOLS_MIN = 7  # UM futures: agg_id, price, qty, first_id, last_id, ts, is_buyer_maker

# Timestamps at or above this threshold are in microseconds (2025+ series).
# Below this threshold are in milliseconds (pre-2025 series).
# 10^15 = 2001-09-08 in microseconds; any plausible crypto timestamp in ms
# is safely below 10^15 (2033-05-18 limit), so the boundary is unambiguous.
US_THRESHOLD: int = 1_000_000_000_000_000

HOURLY_HEADER = (
    "timestamp_utc", "open", "high", "low", "close",
    "taker_buy_vol", "taker_sell_vol",
)


@dataclass
class HourBin:
    """Accumulated OHLCV + flow data for one UTC hour."""
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    taker_buy_vol: Decimal = field(default_factory=lambda: Decimal("0"))
    taker_sell_vol: Decimal = field(default_factory=lambda: Decimal("0"))


# ---------------------------------------------------------------------------
# Public URL builders
# ---------------------------------------------------------------------------

def monthly_url(symbol: str, year: int, month: int) -> str:
    """Return the data.binance.vision URL for a monthly aggTrades zip."""
    return _MONTHLY_URL.format(
        base=_BASE_URL, symbol=symbol, year=year, month=month,
    )


def daily_url(symbol: str, year: int, month: int, day: int) -> str:
    """Return the data.binance.vision URL for a daily aggTrades zip."""
    return _DAILY_URL.format(
        base=_BASE_URL, symbol=symbol, year=year, month=month, day=day,
    )


# ---------------------------------------------------------------------------
# Timestamp unit detection
# ---------------------------------------------------------------------------

def detect_ts_unit(ts_int: int) -> str:
    """Return 'us' if timestamp is in microseconds, 'ms' if milliseconds."""
    return "us" if ts_int >= US_THRESHOLD else "ms"


def _ts_to_hour_ms(ts_int: int, unit: str) -> int:
    """Floor a raw timestamp to the start-of-UTC-hour, returning epoch milliseconds."""
    ms = ts_int // 1000 if unit == "us" else ts_int
    return (ms // 3_600_000) * 3_600_000


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_is_buyer_maker(value: str) -> bool:
    v = value.strip().lower()
    if v == "true":
        return True
    if v == "false":
        return False
    raise ValueError(f"invalid isBuyerMaker value: {value!r}")


def parse_aggtrades_zip(
    data: bytes,
) -> tuple[str, list[tuple[int, Decimal, Decimal, bool]]]:
    """Extract and parse aggTrade rows from a data.binance.vision zip archive.

    Returns (ts_unit, rows) where:
      ts_unit: 'ms' or 'us' (detected from first data row)
      rows:    list of (raw_timestamp_int, price, qty, is_buyer_maker)
               in chronological order as stored in the zip
    """
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(
                f"zip contains no .csv file; entries: {zf.namelist()!r}"
            )
        raw = zf.read(csv_names[0]).decode("utf-8")

    rows: list[tuple[int, Decimal, Decimal, bool]] = []
    unit: str | None = None

    for line in csv.reader(io.StringIO(raw)):
        if not line or not line[0].strip():
            continue
        # Skip header rows (non-numeric first field, e.g. "agg_trade_id")
        first = line[0].strip().lstrip("-")
        if not first.isdigit():
            continue
        if len(line) < _NCOLS_MIN:
            raise ValueError(
                f"aggTrades row has {len(line)} columns; expected >= {_NCOLS_MIN}: {line!r}"
            )
        try:
            ts_int = int(line[5])
            price = Decimal(line[1])
            qty = Decimal(line[2])
            is_buyer_maker = _parse_is_buyer_maker(line[6])
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"invalid aggTrades row {line!r}: {exc}") from exc

        if unit is None:
            unit = detect_ts_unit(ts_int)
        rows.append((ts_int, price, qty, is_buyer_maker))

    return (unit or "ms"), rows


# ---------------------------------------------------------------------------
# Hourly aggregation
# ---------------------------------------------------------------------------

def aggregate_to_hourly(
    rows: list[tuple[int, Decimal, Decimal, bool]],
    *,
    unit: str,
) -> dict[int, HourBin]:
    """Aggregate raw aggTrade rows into per-UTC-hour HourBin objects.

    Rows must arrive in chronological order (as they come from the zip).
    The first row for each hour sets the open; subsequent rows update
    high, low, close, and volume accumulators.
    Returns dict keyed by UTC hour-start epoch milliseconds.
    """
    bins: dict[int, HourBin] = {}
    for ts_int, price, qty, is_buyer_maker in rows:
        hour_ms = _ts_to_hour_ms(ts_int, unit)
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
    return bins


# ---------------------------------------------------------------------------
# Download entry-point
# ---------------------------------------------------------------------------

def download_aggtrades_hourly(
    *,
    symbol: str,
    output_dir: Path | str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Path:
    """Download USD-M perp aggTrades and aggregate to 1-hour bins.

    Uses monthly zips for complete elapsed months; daily zips for the current
    (incomplete) month. Raw ticks are aggregated in memory and never written
    to disk. 404 responses are silently skipped.

    Returns the path of the written hourly CSV file.
    """
    if not symbol:
        raise ValueError("symbol must not be empty")

    today = date.today()
    if end_date is None:
        end_date = today - timedelta(days=1)
    if start_date is None:
        start_date = date(2019, 9, 1)  # earliest USD-M perp aggTrades data

    all_bins: dict[int, HourBin] = {}

    year, month = start_date.year, start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        is_current = year == today.year and month == today.month
        if not is_current:
            url = monthly_url(symbol, year, month)
            _download_and_merge(url, all_bins)
        else:
            d = date(year, month, 1)
            while d <= end_date and d.month == month:
                url = daily_url(symbol, year, month, d.day)
                _download_and_merge(url, all_bins)
                d += timedelta(days=1)

        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{symbol}_aggtrades_1h.csv"

    sorted_hours = sorted(all_bins)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HOURLY_HEADER)
        for hour_ms in sorted_hours:
            b = all_bins[hour_ms]
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
    return output_path


def _download_and_merge(url: str, bins: dict[int, HourBin]) -> None:
    """Download one zip, aggregate to hourly bins, merge into existing bins."""
    req = urllib.request.Request(url, headers={"User-Agent": "research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise

    unit, rows = parse_aggtrades_zip(data)
    new_bins = aggregate_to_hourly(rows, unit=unit)

    # Monthly files are non-overlapping so a simple merge suffices.
    # In the edge case of overlap (daily vs monthly boundary), prefer the
    # existing open price and take the later close / merged volumes.
    for hour_ms, new_bin in new_bins.items():
        if hour_ms not in bins:
            bins[hour_ms] = new_bin
        else:
            existing = bins[hour_ms]
            existing.high = max(existing.high, new_bin.high)
            existing.low = min(existing.low, new_bin.low)
            existing.close = new_bin.close
            existing.taker_buy_vol += new_bin.taker_buy_vol
            existing.taker_sell_vol += new_bin.taker_sell_vol
