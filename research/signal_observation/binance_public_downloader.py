"""Binance USDT-M Futures public kline downloader for local research CSV inputs."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence


BINANCE_FUTURES_KLINES_URL = "https://fapi.binance.com/fapi/v1/klines"
SUPPORTED_INTERVALS = ("1h", "4h")
CSV_HEADER = ("timestamp", "open", "high", "low", "close", "volume")


def download_binance_futures_klines(
    *,
    symbol: str,
    interval: str,
    output_csv: str | Path,
    limit: int = 1500,
    start_time: str | int | None = None,
    end_time: str | int | None = None,
    max_pages: int = 1,
) -> Path:
    """Download Binance USDT-M Futures public klines and write a local OHLCV CSV.

    Two modes:

    Single-page: ``start_time`` and ``end_time`` both ``None``. Fetches one
    page from the most recent klines and writes the rows ascending by open
    time. ``max_pages`` is ignored.

    Bounded pagination: supply both ``start_time`` and ``end_time`` as
    millisecond-epoch strings or ints. Pages forward using Binance's
    ``startTime``/``endTime`` semantics until ``end_time`` is reached, no
    more rows are returned, fewer than ``limit`` rows are returned, or
    ``max_pages`` is hit. Rows are filtered to ``start_time <= open_ms <=
    end_time`` and de-duplicated by open time.
    """

    if not symbol:
        raise ValueError("symbol must not be empty")
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(
            f"interval must be one of: {SUPPORTED_INTERVALS}"
        )
    if not 1 <= limit <= 1500:
        raise ValueError("limit must be between 1 and 1500")
    if max_pages <= 0:
        raise ValueError("max_pages must be positive")

    start_set = start_time is not None
    end_set = end_time is not None
    if start_set ^ end_set:
        raise ValueError(
            "bounded pagination requires both start_time and end_time"
        )

    if start_set and end_set:
        return _download_bounded(
            symbol=symbol,
            interval=interval,
            output_csv=output_csv,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            max_pages=max_pages,
        )

    return _download_single_page(
        symbol=symbol,
        interval=interval,
        output_csv=output_csv,
        limit=limit,
    )


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for Binance USDT-M Futures public kline CSV downloads."""

    parser = argparse.ArgumentParser(
        description="Download Binance USDT-M Futures public klines to local CSV."
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--interval", required=True, choices=SUPPORTED_INTERVALS)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=1500)
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--max-pages", type=int, default=1)
    args = parser.parse_args(argv)

    output_path = download_binance_futures_klines(
        symbol=args.symbol,
        interval=args.interval,
        output_csv=args.output,
        limit=args.limit,
        start_time=args.start_time,
        end_time=args.end_time,
        max_pages=args.max_pages,
    )
    print(f"wrote: {output_path}")


def _download_single_page(
    *,
    symbol: str,
    interval: str,
    output_csv: str | Path,
    limit: int,
) -> Path:
    raw_rows = _fetch_page(
        symbol=symbol,
        interval=interval,
        limit=limit,
        start_time=None,
        end_time=None,
    )
    parsed = [_parse_binance_row(row) for row in raw_rows]
    parsed.sort(key=lambda row: row[0])

    output_path = Path(output_csv)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        writer.writerows(parsed)
    return output_path


def _download_bounded(
    *,
    symbol: str,
    interval: str,
    output_csv: str | Path,
    limit: int,
    start_time: str | int,
    end_time: str | int,
    max_pages: int,
) -> Path:
    start_ms = _timestamp_ms("start_time", start_time)
    end_ms = _timestamp_ms("end_time", end_time)
    if start_ms >= end_ms:
        raise ValueError("start_time must be strictly before end_time")

    confirmed: dict[int, tuple[str, str, str, str, str, str]] = {}
    current_start = start_ms

    for _page in range(max_pages):
        raw_rows = _fetch_page(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=current_start,
            end_time=end_ms,
        )
        if not raw_rows:
            break

        page_latest_ms: int | None = None
        for raw in raw_rows:
            open_ms = _timestamp_ms("response open_time", raw[0])
            page_latest_ms = (
                open_ms if page_latest_ms is None else max(page_latest_ms, open_ms)
            )
            if not (start_ms <= open_ms <= end_ms):
                continue
            confirmed[open_ms] = _parse_binance_row(raw)

        if page_latest_ms is None:
            break
        if page_latest_ms >= end_ms:
            break
        if len(raw_rows) < limit:
            break
        current_start = page_latest_ms + 1

    output_rows = [confirmed[ts] for ts in sorted(confirmed)]

    output_path = Path(output_csv)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        writer.writerows(output_rows)
    return output_path


def _fetch_page(
    *,
    symbol: str,
    interval: str,
    limit: int,
    start_time: int | None,
    end_time: int | None,
) -> list[Sequence]:
    params: dict[str, str] = {
        "symbol": symbol,
        "interval": interval,
        "limit": str(limit),
    }
    if start_time is not None:
        params["startTime"] = str(start_time)
    if end_time is not None:
        params["endTime"] = str(end_time)

    url = BINANCE_FUTURES_KLINES_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        message = body
        try:
            parsed_body = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            parsed_body = None
        if isinstance(parsed_body, dict) and parsed_body.get("msg"):
            message = str(parsed_body.get("msg"))
        raise ValueError(
            f"Binance API HTTP {exc.code}: {message!r}"
        ) from exc

    if isinstance(payload, dict) and "code" in payload:
        raise ValueError(
            "Binance API error: "
            f"code={payload.get('code')!r} msg={payload.get('msg')!r}"
        )
    if not isinstance(payload, list):
        raise ValueError(
            f"unexpected Binance response shape: {type(payload).__name__}"
        )
    return payload


def _parse_binance_row(row: Sequence) -> tuple[str, str, str, str, str, str]:
    if len(row) < 6:
        raise ValueError("Binance kline row is incomplete")
    open_ms = _timestamp_ms("kline open_time", row[0])
    ts_iso = _timestamp_ms_to_iso(open_ms)
    open_ = _decimal_text("open", row[1])
    high = _decimal_text("high", row[2])
    low = _decimal_text("low", row[3])
    close = _decimal_text("close", row[4])
    volume = _decimal_text("volume", row[5])
    return ts_iso, open_, high, low, close, volume


def _timestamp_ms_to_iso(timestamp_ms: int) -> str:
    seconds, milliseconds = divmod(timestamp_ms, 1000)
    timestamp = datetime.fromtimestamp(seconds, tz=UTC)
    if milliseconds:
        timestamp = timestamp.replace(microsecond=milliseconds * 1000)
    return timestamp.isoformat().replace("+00:00", "Z")


def _timestamp_ms(name: str, value: str | int) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {name}: {value!r}") from exc


def _decimal_text(name: str, value: object) -> str:
    try:
        return str(Decimal(str(value)))
    except InvalidOperation as exc:
        raise ValueError(f"invalid {name}: {value!r}") from exc


if __name__ == "__main__":
    main()
