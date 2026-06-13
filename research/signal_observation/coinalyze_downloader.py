"""Coinalyze liquidation-history and OHLCV downloader for Setup E research.

Endpoint contracts verified against the Coinalyze reference client source at
https://github.com/ivarurdalen/coinalyze (verified 2026-06-13):

  Base URL         : https://api.coinalyze.net/v1/
  Auth             : request header  api_key  (lowercase); same name as query param
  4H interval      : "4hour"  (Interval.H4 = "4hour" in the reference enums)
  from / to params : POSIX seconds (int)
  Response t field : POSIX SECONDS (verified live 2026-06-13: diff between adjacent
                     4H bars = 14400 s; reference-client test fixture used ms, misleading)
  OHLCV fields     : t, o, h, l (low price — NOT long), c, v, bv, tx, btx
  Liquidation      : t, l (long notional), s (short notional)
                     pass convert_to_usd=true for USD-denominated values
  Rate limit       : 40 weighted calls per minute; a request with N symbols costs N
  HTTP 429         : Retry-After header present; retried here with exponential backoff
  Max symbols      : 20 per request
  4H history depth : rolling ~1500–2000 bars (≈250–330 days); full history
                     retrieved via reverse-chronological paging

Output CSV format (both files):
  OHLCV        : timestamp, open, high, low, close, volume
  Liquidation  : timestamp_utc, long_notional_usd, short_notional_usd
  timestamp    : bar OPEN time UTC (constitution §3.1), ISO 8601 format

Files written to research/signal_observation/data/setup_e/ by default.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence


_BASE_URL = "https://api.coinalyze.net/v1"
_INTERVAL_4H = "4hour"
_MAX_SYMBOLS = 20
_RATE_LIMIT_WEIGHT_PER_MIN = 40
_RETRY_MAX = 5
_RETRY_INITIAL_BACKOFF_S = 5.0
# Conservative epoch: Coinalyze coverage starts ~2019
_HISTORY_EPOCH_YEAR = 2019

# CSV headers — OHLCV column names match REQUIRED_COLUMNS in csv_loader.py
OHLCV_CSV_HEADER = ("timestamp", "open", "high", "low", "close", "volume")
LIQUIDATION_CSV_HEADER = ("timestamp_utc", "long_notional_usd", "short_notional_usd")

_SETUP_E_DATA_DIR = Path(__file__).parent / "data" / "setup_e"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def require_api_key() -> str:
    """Return COINALYZE_API_KEY from environment; raise EnvironmentError if unset."""
    key = os.environ.get("COINALYZE_API_KEY", "").strip()
    if not key:
        raise EnvironmentError(
            "COINALYZE_API_KEY is not set. "
            "Generate a free key at https://coinalyze.net/account/api-key/ "
            "and add it to your .env file. Never commit or log the key."
        )
    return key


# ---------------------------------------------------------------------------
# Internal HTTP
# ---------------------------------------------------------------------------

def _s_to_iso(ts_s: int) -> str:
    """POSIX seconds → ISO 8601 UTC string (bar OPEN time)."""
    return datetime.fromtimestamp(ts_s, tz=UTC).isoformat().replace("+00:00", "Z")


def _throttle(n_symbols: int) -> None:
    """Conservative sleep to respect the 40-weighted-calls/minute rate limit.

    A request for N symbols consumes N of the 40-per-minute budget. Sleep
    proportionally with a 20 % safety margin.
    """
    seconds = (n_symbols / _RATE_LIMIT_WEIGHT_PER_MIN) * 60.0 * 1.2
    time.sleep(seconds)


def _api_get(endpoint: str, params: dict, api_key: str) -> list:
    """Make one authenticated GET; retry on 429 with Retry-After / backoff."""
    url = f"{_BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"api_key": api_key, "Accept": "application/json"}
    )
    backoff = _RETRY_INITIAL_BACKOFF_S
    for _attempt in range(_RETRY_MAX):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                hdrs = exc.headers
                retry_after_str = hdrs.get("Retry-After") if hdrs else None
                wait = float(retry_after_str) if retry_after_str else backoff
                time.sleep(wait)
                backoff = min(backoff * 2, 120.0)
            else:
                body = exc.read().decode("utf-8", errors="ignore")
                raise ValueError(f"Coinalyze HTTP {exc.code}: {body!r}") from exc
    raise ValueError(
        f"Coinalyze API returned 429 on all {_RETRY_MAX} retry attempts"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_perpetual_symbols(api_key: str) -> list[dict]:
    """Return all futures/perpetual markets Coinalyze supports.

    Each entry has keys: symbol, exchange, symbol_on_exchange, base_asset,
    quote_asset.
    """
    return _api_get("future-markets", {}, api_key)


def _fetch_history_page(
    endpoint: str,
    symbols: list[str],
    from_s: int,
    to_s: int,
    api_key: str,
    extra: dict | None = None,
) -> list[dict]:
    if len(symbols) > _MAX_SYMBOLS:
        raise ValueError(f"At most {_MAX_SYMBOLS} symbols per request; got {len(symbols)}")
    params: dict = {
        "symbols": ",".join(symbols),
        "interval": _INTERVAL_4H,
        "from": str(from_s),
        "to": str(to_s),
    }
    if extra:
        params.update(extra)
    return _api_get(endpoint, params, api_key)


def _full_history(
    endpoint: str,
    symbols: list[str],
    api_key: str,
    extra: dict | None = None,
) -> dict[str, list[dict]]:
    """Fetch all available history via reverse-chronological paging.

    Returns {symbol_id: [bar, ...]} sorted ascending by bar timestamp.
    Pagination: after each page, advance the upper-bound (to) to just before
    the oldest bar received. Stops when a page yields no new bars.
    """
    epoch_s = int(datetime(_HISTORY_EPOCH_YEAR, 1, 1, tzinfo=UTC).timestamp())
    now_s = int(datetime.now(UTC).timestamp())

    seen: dict[str, set] = {s: set() for s in symbols}
    bars: dict[str, list[dict]] = {s: [] for s in symbols}
    to_s = now_s

    while True:
        page = _fetch_history_page(endpoint, symbols, epoch_s, to_s, api_key, extra)

        new_count = 0
        page_oldest_s: int | None = None

        for sym_data in page:
            sym = sym_data.get("symbol", "")
            if sym not in bars:
                continue
            for bar in sym_data.get("history", []):
                t: int = bar["t"]
                if t not in seen[sym]:
                    seen[sym].add(t)
                    bars[sym].append(bar)
                    new_count += 1
                if page_oldest_s is None or t < page_oldest_s:
                    page_oldest_s = t

        if new_count == 0 or page_oldest_s is None:
            break

        next_to_s = page_oldest_s - 1
        if next_to_s <= epoch_s or next_to_s >= to_s:
            break
        to_s = next_to_s
        _throttle(len(symbols))

    for sym in bars:
        bars[sym].sort(key=lambda b: b["t"])
    return bars


def fetch_ohlcv_4h_history(symbols: list[str], api_key: str) -> dict[str, list[dict]]:
    """Fetch full available 4H OHLCV history for up to 20 symbols at once."""
    return _full_history("ohlcv-history", symbols, api_key)


def fetch_liquidation_4h_history(
    symbols: list[str], api_key: str
) -> dict[str, list[dict]]:
    """Fetch full available 4H liquidation history (USD notional) for up to 20 symbols."""
    return _full_history(
        "liquidation-history", symbols, api_key, {"convert_to_usd": "true"}
    )


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def write_ohlcv_csv(bars: list[dict], path: Path) -> Path:
    """Write OHLCV bars to CSV. timestamp = bar OPEN time UTC (constitution §3.1)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(OHLCV_CSV_HEADER)
        for b in bars:
            w.writerow([_s_to_iso(b["t"]), b["o"], b["h"], b["l"], b["c"], b["v"]])
    return path


def write_liquidation_csv(bars: list[dict], path: Path) -> Path:
    """Write liquidation bars to CSV. l = long notional USD, s = short notional USD."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(LIQUIDATION_CSV_HEADER)
        for b in bars:
            w.writerow([_s_to_iso(b["t"]), b["l"], b["s"]])
    return path


# ---------------------------------------------------------------------------
# Batch download
# ---------------------------------------------------------------------------

def _symbol_to_filename(symbol_id: str) -> str:
    return symbol_id.replace("/", "_").replace(".", "_")


def download_setup_e(
    symbols: list[str],
    api_key: str,
    output_dir: Path | None = None,
) -> dict[str, tuple[Path, Path]]:
    """Download 4H OHLCV + liquidation CSVs for each symbol.

    Fetches both datasets in a single batch request per dataset type, then
    writes per-symbol CSVs. Returns {symbol: (ohlcv_path, liq_path)}.
    """
    out = output_dir or _SETUP_E_DATA_DIR
    ohlcv_data = fetch_ohlcv_4h_history(symbols, api_key)
    _throttle(len(symbols))
    liq_data = fetch_liquidation_4h_history(symbols, api_key)

    result: dict[str, tuple[Path, Path]] = {}
    for sym in symbols:
        fname = _symbol_to_filename(sym)
        ohlcv_path = write_ohlcv_csv(
            ohlcv_data.get(sym, []), out / f"{fname}_ohlcv_4h.csv"
        )
        liq_path = write_liquidation_csv(
            liq_data.get(sym, []), out / f"{fname}_liquidation_4h.csv"
        )
        result[sym] = (ohlcv_path, liq_path)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> None:
    """CLI: download Coinalyze 4H OHLCV + liquidation CSVs for Setup E."""
    parser = argparse.ArgumentParser(
        description=(
            "Download Coinalyze 4H OHLCV and liquidation history for Setup E. "
            "Requires COINALYZE_API_KEY in environment."
        )
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
        help="Coinalyze symbol IDs (max 20), e.g. BTCUSDT_PERP.A",
    )
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)

    api_key = require_api_key()
    out_dir = Path(args.output_dir) if args.output_dir else None
    paths = download_setup_e(args.symbols, api_key, out_dir)
    for sym, (ohlcv, liq) in paths.items():
        print(f"{sym}: ohlcv={ohlcv}  liq={liq}")


if __name__ == "__main__":
    main()
