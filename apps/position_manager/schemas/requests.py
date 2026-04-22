from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from libs.schemas.common import ExecutionStatus, PositionCloseReason, TradeDirection


class PositionOpenRequest(BaseModel):
    execution_id: str
    execution_status: ExecutionStatus
    symbol: str
    side: TradeDirection
    quantity: float = Field(gt=0)
    entry_price: float = Field(gt=0)
    stop_loss: float | None = None
    take_profit: list[float] = Field(default_factory=list)
    opened_at: datetime
    ttl_expires_at: datetime | None = None
    candidate_id: str | None = None
    signal_id: str | None = None
    correlation_id: str


class PositionCloseRequest(BaseModel):
    position_id: str
    reason: PositionCloseReason
    close_price: float | None = Field(default=None, gt=0)
    closed_at: datetime
    correlation_id: str


class ExchangePositionSnapshot(BaseModel):
    position_id: str | None = None
    execution_id: str | None = None
    symbol: str
    side: TradeDirection
    quantity: float = Field(gt=0)
    entry_price: float = Field(gt=0)
    mark_price: float | None = Field(default=None, gt=0)
    opened_at: datetime | None = None
    ttl_expires_at: datetime | None = None
    status: str = "open"


class ReconcileRequest(BaseModel):
    exchange_positions: list[ExchangePositionSnapshot] = Field(default_factory=list)
    correlation_id: str
