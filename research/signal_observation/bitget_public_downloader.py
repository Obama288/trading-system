"""Bitget public market candle downloader for local research CSV inputs."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence


BITGET_HISTORY_CANDLES_URL = (
    "https://api.bitget.com/api/v2/mix/market/history-candles"
)
SUPPORTED_GRANULARITIES = ("1H", "4H")
SUPPORTED_PRODUCT_TYPES = ("USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES")
CSV_HEADER = ("timestamp", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class _ParsedCandle:
    timestamp_ms: int
    csv_row: tuple[str, str, str, str, str, str]


def download_bitget_history_candles(
    *,
    symbol: str,
    product_type: str,
    granularity: str,
    output_csv: str | Path,
    limit: int = 200,
    start_time: str | None = None,
    end_time: str | None = None,
    max_pages: int = 1,
) -> Path:
    """Download Bitget public historical candles and write local OHLCV CSV."""

    if not symbol:
        raise ValueError("symbol must not be empty")
    if product_type not in SUPPORTED_PRODUCT_TYPES:
        raise ValueError("product_type must be one of: USDT-FUTURES, COIN-FUTURES, USDC-FUTURES")
    if granularity not in SUPPORTED_GRANULARITIES:
        raise ValueError("granularity must be one of: 1H, 4H")
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    if max_pages <= 0:
        raise ValueError("max_pages must be positive")
    current_start_time = _optional_timestamp_ms("start_time", start_time)
    current_end_time = _optional_timestamp_ms("end_time", end_time)

    candles_by_timestamp: dict[int, tuple[str, str, str, str, str, str]] = {}
    page_mode = "forward" if current_start_time is not None else "backward"

    for _page_number in range(max_pages):
        payload = _fetch_page(
            symbol=symbol,
            product_type=product_type,
            granularity=granularity,
            limit=limit,
            start_time=current_start_time,
            end_time=current_end_time,
        )
        parsed_page = [_parse_bitget_row(row) for row in payload.get("data", [])]
        if not parsed_page:
            break

        for candle in parsed_page:
            candles_by_timestamp[candle.timestamp_ms] = candle.csv_row

        timestamps = [candle.timestamp_ms for candle in parsed_page]
        oldest = min(timestamps)
        newest = max(timestamps)
        if len(parsed_page) < limit:
            break

        if page_mode == "forward":
            next_start_time = newest + 1
            if current_end_time is not None and next_start_time > current_end_time:
                break
            if current_start_time is not None and next_start_time <= current_start_time:
                break
            current_start_time = next_start_time
        else:
            next_end_time = oldest - 1
            if current_end_time is not None and next_end_time >= current_end_time:
                break
            current_end_time = next_end_time

    rows = [
        candles_by_timestamp[timestamp]
        for timestamp in sorted(candles_by_timestamp)
    ]

    output_path = Path(output_csv)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)

    return output_path


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for Bitget public candle CSV downloads."""

    parser = argparse.ArgumentParser(
        description="Download Bitget public historical candles to local CSV."
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--product-type", required=True, choices=SUPPORTED_PRODUCT_TYPES)
    parser.add_argument("--granularity", required=True, choices=SUPPORTED_GRANULARITIES)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--max-pages", type=int, default=1)
    args = parser.parse_args(argv)

    output_path = download_bitget_history_candles(
        symbol=args.symbol,
        product_type=args.product_type,
        granularity=args.granularity,
        output_csv=args.output,
        limit=args.limit,
        start_time=args.start_time,
        end_time=args.end_time,
        max_pages=args.max_pages,
    )
    print(f"wrote: {output_path}")


def _fetch_page(
    *,
    symbol: str,
    product_type: str,
    granularity: str,
    limit: int,
    start_time: int | None,
    end_time: int | None,
) -> dict:
    params = {
        "symbol": symbol,
        "productType": product_type,
        "granularity": granularity,
        "limit": str(limit),
    }
    if start_time is not None:
        params["startTime"] = str(start_time)
    if end_time is not None:
        params["endTime"] = str(end_time)

    url = f"{BITGET_HISTORY_CANDLES_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("code") != "00000":
        message = payload.get("msg") or "Bitget public candle response failed"
        raise ValueError(message)
    return payload


def _parse_bitget_row(row: Sequence[str]) -> _ParsedCandle:
    if len(row) < 7:
        raise ValueError("Bitget candle row is incomplete")

    timestamp_ms = _timestamp_ms("timestamp", row[0])
    timestamp = _timestamp_ms_to_iso(timestamp_ms)
    open_ = _decimal_text("open", row[1])
    high = _decimal_text("high", row[2])
    low = _decimal_text("low", row[3])
    close = _decimal_text("close", row[4])
    volume = _decimal_text("volume", row[5])
    return _ParsedCandle(
        timestamp_ms=timestamp_ms,
        csv_row=(timestamp, open_, high, low, close, volume),
    )


def _optional_timestamp_ms(name: str, value: str | None) -> int | None:
    if value is None:
        return None
    return _timestamp_ms(name, value)


def _timestamp_ms(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {value!r}") from exc


def _timestamp_ms_to_iso(timestamp_ms: int) -> str:
    seconds, milliseconds = divmod(timestamp_ms, 1000)
    timestamp = datetime.fromtimestamp(seconds, tz=UTC)
    if milliseconds:
        timestamp = timestamp.replace(microsecond=milliseconds * 1000)
    return timestamp.isoformat().replace("+00:00", "Z")


def _decimal_text(name: str, value: str) -> str:
    try:
        return str(Decimal(str(value)))
    except InvalidOperation as exc:
        raise ValueError(f"invalid {name}: {value!r}") from exc


if __name__ == "__main__":
    main()
