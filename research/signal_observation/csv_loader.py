"""Local CSV OHLCV loader for research-layer signal observation."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .candles import Candle, parse_iso_utc


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


def _normalize_header(value: str | None) -> str:
    return (value or "").strip().lower()


def _parse_decimal(row_number: int, column: str, value: str | None) -> Decimal:
    raw_value = (value or "").strip()
    if not raw_value:
        raise ValueError(f"row {row_number}: {column} must not be empty")
    try:
        return Decimal(raw_value)
    except InvalidOperation as exc:
        raise ValueError(f"row {row_number}: invalid {column}: {raw_value!r}") from exc


def load_ohlcv_csv(path: str | Path) -> list[Candle]:
    """Load local OHLCV CSV data into sorted Candle objects."""

    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty")

        normalized_headers = tuple(_normalize_header(name) for name in reader.fieldnames)
        if set(normalized_headers) != set(REQUIRED_COLUMNS):
            missing = sorted(set(REQUIRED_COLUMNS) - set(normalized_headers))
            extra = sorted(set(normalized_headers) - set(REQUIRED_COLUMNS))
            parts: list[str] = []
            if missing:
                parts.append(f"missing columns: {', '.join(missing)}")
            if extra:
                parts.append(f"unexpected columns: {', '.join(extra)}")
            raise ValueError("; ".join(parts) or "invalid CSV header")

        header_map = dict(zip(reader.fieldnames, normalized_headers, strict=True))
        candles: list[Candle] = []
        seen_timestamps = set()

        for row_number, row in enumerate(reader, start=2):
            normalized_row = {
                header_map[name]: value for name, value in row.items() if name is not None
            }
            timestamp = parse_iso_utc(normalized_row.get("timestamp", ""))
            if timestamp in seen_timestamps:
                raise ValueError(f"row {row_number}: duplicate timestamp")
            seen_timestamps.add(timestamp)

            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=_parse_decimal(row_number, "open", normalized_row.get("open")),
                    high=_parse_decimal(row_number, "high", normalized_row.get("high")),
                    low=_parse_decimal(row_number, "low", normalized_row.get("low")),
                    close=_parse_decimal(row_number, "close", normalized_row.get("close")),
                    volume=_parse_decimal(
                        row_number, "volume", normalized_row.get("volume")
                    ),
                )
            )

    if not candles:
        raise ValueError("CSV file contains no candles")
    return sorted(candles, key=lambda candle: candle.timestamp)
