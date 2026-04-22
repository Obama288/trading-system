from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from libs.schemas.common import PositionCloseReason, PositionStatus, TradeDirection


@dataclass(slots=True)
class Position:
    position_id: str
    execution_id: str
    symbol: str
    side: TradeDirection
    status: PositionStatus
    quantity: float
    entry_price: float
    stop_loss: float | None = None
    take_profit: list[float] = field(default_factory=list)
    opened_at: datetime | None = None
    ttl_expires_at: datetime | None = None
    candidate_id: str | None = None
    signal_id: str | None = None
    closed_at: datetime | None = None
    close_price: float | None = None
    close_reason: PositionCloseReason | None = None

    @property
    def is_open(self) -> bool:
        return self.status == PositionStatus.OPEN
