"""OKX public market candle downloader for local research CSV inputs."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence


OKX_HISTORY_CANDLES_URL = "https://www.okx.com/api/v5/market/history-candles"
SUPPORTED_BARS = ("1H", "4H")
CSV_HEADER = ("timestamp", "open", "high", "low", "close", "volume")


def download_okx_history_candles(
    *,
    inst_id: str,
    bar: str,
    output_csv: str | Path,
    limit: int = 300,
    before: str | None = None,
    after: str | None = None,
) -> Path:
    """Download OKX public historical candles and write local OHLCV CSV."""

    if not inst_id:
        raise ValueError("inst_id must not be empty")
    if bar not in SUPPORTED_BARS:
        raise ValueError("bar must be one of: 1H, 4H")
    if not 1 <= limit <= 300:
        raise ValueError("limit must be between 1 and 300")

    params = {
        "instId": inst_id,
        "bar": bar,
        "limit": str(limit),
    }
    if before is not None:
        params["before"] = before
    if after is not None:
        params["after"] = after

    url = f"{OKX_HISTORY_CANDLES_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("code") != "0":
        message = payload.get("msg") or "OKX public candle response failed"
        raise ValueError(message)

    rows = [_parse_okx_row(row) for row in payload.get("data", [])]
    confirmed_rows = [row for row in rows if row[-1] == "1"]
    confirmed_rows.sort(key=lambda row: row[0])

    output_path = Path(output_csv)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        for timestamp, open_, high, low, close, volume, _confirm in confirmed_rows:
            writer.writerow([timestamp, open_, high, low, close, volume])

    return output_path


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for OKX public candle CSV downloads."""

    parser = argparse.ArgumentParser(
        description="Download OKX public historical candles to local CSV."
    )
    parser.add_argument("--inst-id", required=True)
    parser.add_argument("--bar", required=True, choices=SUPPORTED_BARS)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--before")
    parser.add_argument("--after")
    args = parser.parse_args(argv)

    output_path = download_okx_history_candles(
        inst_id=args.inst_id,
        bar=args.bar,
        output_csv=args.output,
        limit=args.limit,
        before=args.before,
        after=args.after,
    )
    print(f"wrote: {output_path}")


def _parse_okx_row(row: Sequence[str]) -> tuple[str, str, str, str, str, str, str]:
    if len(row) < 9:
        raise ValueError("OKX candle row is incomplete")

    timestamp = _timestamp_ms_to_iso(row[0])
    open_ = _decimal_text("open", row[1])
    high = _decimal_text("high", row[2])
    low = _decimal_text("low", row[3])
    close = _decimal_text("close", row[4])
    volume = _decimal_text("volume", row[5])
    confirm = str(row[8])
    return timestamp, open_, high, low, close, volume, confirm


def _timestamp_ms_to_iso(value: str) -> str:
    try:
        timestamp_ms = int(value)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc
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
