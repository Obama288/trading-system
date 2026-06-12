"""Candle data model for research-layer signal observation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


def normalize_utc(timestamp: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def parse_iso_utc(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and normalize it to UTC."""

    normalized = value.strip()
    if not normalized:
        raise ValueError("timestamp must not be empty")
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        return normalize_utc(datetime.fromisoformat(normalized))
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc


def _ensure_decimal(name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")


@dataclass(frozen=True, slots=True)
class Candle:
    """Single OHLCV candle from public historical data."""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", normalize_utc(self.timestamp))

        _ensure_decimal("open", self.open)
        _ensure_decimal("high", self.high)
        _ensure_decimal("low", self.low)
        _ensure_decimal("close", self.close)
        _ensure_decimal("volume", self.volume)

        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be greater than or equal to open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be less than or equal to open, close, and high")
        if self.volume < Decimal("0"):
            raise ValueError("volume must be greater than or equal to zero")
