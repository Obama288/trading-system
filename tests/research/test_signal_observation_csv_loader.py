from __future__ import annotations

from datetime import UTC
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from research.signal_observation import Candle, load_ohlcv_csv


FIXTURE_DIR = Path("tests/fixtures/signal_observation")


def _load_csv_text(content: str) -> list[Candle]:
    with patch.object(Path, "open", return_value=StringIO(content)):
        return load_ohlcv_csv("memory.csv")


def test_loads_valid_csv_into_candle_objects() -> None:
    candles = load_ohlcv_csv(FIXTURE_DIR / "sample_1h.csv")

    assert candles
    assert all(isinstance(candle, Candle) for candle in candles)


def test_ohlcv_fields_are_decimal() -> None:
    candle = load_ohlcv_csv(FIXTURE_DIR / "sample_1h.csv")[0]

    assert isinstance(candle.open, Decimal)
    assert isinstance(candle.high, Decimal)
    assert isinstance(candle.low, Decimal)
    assert isinstance(candle.close, Decimal)
    assert isinstance(candle.volume, Decimal)


def test_timestamps_are_sorted_ascending_and_utc() -> None:
    candles = load_ohlcv_csv(FIXTURE_DIR / "sample_1h.csv")
    timestamps = [candle.timestamp for candle in candles]

    assert timestamps == sorted(timestamps)
    assert all(timestamp.tzinfo is UTC for timestamp in timestamps)


def test_rejects_missing_required_column() -> None:
    content = (
        "timestamp,open,high,low,close\n"
        "2026-05-01T00:00:00Z,100,101,99,100.5\n",
    )

    with pytest.raises(ValueError, match="missing columns: volume"):
        _load_csv_text("".join(content))


def test_rejects_invalid_decimal_values() -> None:
    content = (
        "timestamp,open,high,low,close,volume\n"
        "2026-05-01T00:00:00Z,100,not-a-decimal,99,100.5,12\n",
    )

    with pytest.raises(ValueError, match="invalid high"):
        _load_csv_text("".join(content))


def test_rejects_duplicate_timestamps() -> None:
    content = (
        "timestamp,open,high,low,close,volume\n"
        "2026-05-01T00:00:00Z,100,101,99,100.5,12\n"
        "2026-05-01T00:00:00+00:00,100.5,102,100,101,10\n",
    )

    with pytest.raises(ValueError, match="duplicate timestamp"):
        _load_csv_text("".join(content))


def test_rejects_invalid_ohlc_bounds() -> None:
    content = (
        "timestamp,open,high,low,close,volume\n"
        "2026-05-01T00:00:00Z,100,99,98,100.5,12\n",
    )

    with pytest.raises(ValueError, match="high"):
        _load_csv_text("".join(content))


def test_rejects_empty_file() -> None:
    with pytest.raises(ValueError, match="empty"):
        _load_csv_text("")


def test_rejects_header_only_file() -> None:
    with pytest.raises(ValueError, match="no candles"):
        _load_csv_text("timestamp,open,high,low,close,volume\n")


def test_research_package_has_no_network_or_exchange_imports() -> None:
    package_dir = Path("research/signal_observation")
    forbidden_tokens = (
        "requests",
        "httpx",
        "aiohttp",
        "websocket",
        "websockets",
        "ccxt",
        "socket",
        "libs.exchange",
    )

    for path in package_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{token} found in {path}"
