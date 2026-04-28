from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ServerTime:
    """Bybit server time normalized from the V5 market time endpoint."""

    exchange: str
    time_second: int
    time_nano: int

    @property
    def timestamp_ms(self) -> int:
        return self.time_nano // 1_000_000

    @property
    def as_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=timezone.utc)
