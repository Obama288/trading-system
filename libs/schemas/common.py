from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class SystemMode(str, Enum):
    OBSERVE = "observe"
    APPROVAL = "approval"
    LIMITED_AUTO = "limited_auto"
    HALTED = "halted"


class TradeDirection(str, Enum):
    LONG = "long"
    SHORT = "short"
    NONE = "none"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


def trade_direction_to_order_side(direction: TradeDirection) -> OrderSide:
    if direction == TradeDirection.LONG:
        return OrderSide.BUY
    if direction == TradeDirection.SHORT:
        return OrderSide.SELL
    raise ValueError("TradeDirection.NONE cannot be converted to an executable order side")

# Usage rule:
# this converter must be used exactly at the boundary where a reviewed trade candidate
# becomes an executable order payload for ExecutionCandidate / execution-service.


class SignalStatus(str, Enum):
    CANDIDATE = "candidate"
    NO_TRADE = "no_trade"
    REJECTED = "rejected"


class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AnomalyFlag(str, Enum):
    STOP_TOO_TIGHT_FOR_ATR = "STOP_TOO_TIGHT_FOR_ATR"
    ENTRY_TOO_CLOSE_TO_RESISTANCE = "ENTRY_TOO_CLOSE_TO_RESISTANCE"
    ENTRY_TOO_CLOSE_TO_SUPPORT = "ENTRY_TOO_CLOSE_TO_SUPPORT"
    MARKET_DATA_STALE = "MARKET_DATA_STALE"
    EXECUTION_CANDIDATE_INCOMPLETE = "EXECUTION_CANDIDATE_INCOMPLETE"
    SIGNAL_RISK_MISMATCH = "SIGNAL_RISK_MISMATCH"


class FilterReason(str, Enum):
    PRICE_INVALID = "PRICE_INVALID"
    ORDERBOOK_TOP_INVALID = "ORDERBOOK_TOP_INVALID"
    LIQUIDITY_NOT_OK = "LIQUIDITY_NOT_OK"
    SPREAD_NOT_OK = "SPREAD_NOT_OK"
    NEWS_RISK = "NEWS_RISK"
    ATR_INVALID = "ATR_INVALID"
    MARKET_DATA_STALE = "MARKET_DATA_STALE"


class ExecutionStatus(str, Enum):
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ServiceEnvelope(BaseModel, Generic[T]):
    ok: bool
    service: str
    version: str = "v1"
    correlation_id: str
    data: T | None = None
    error: dict[str, Any] | None = None


class EntryZone(BaseModel):
    min: float
    max: float


class IndicatorSnapshot(BaseModel):
    ema_20: float
    ema_50: float
    rsi_14: float
    atr_14: float


class MarketFlags(BaseModel):
    news_risk: bool
    liquidity_ok: bool
    spread_ok: bool


class MarketSnapshot(BaseModel):
    symbol: str
    timestamp: datetime
    timeframe: str
    price: float
    bid: float
    ask: float
    spread_bps: float = Field(ge=0.0)
    volatility_regime: str
    trend_regime: str
    session: str
    indicators: IndicatorSnapshot
    market_flags: MarketFlags


class SignalDecision(BaseModel):
    signal_id: str
    status: SignalStatus
    symbol: str
    side: TradeDirection
    setup_type: str
    entry_zone: EntryZone | None = None
    stop_loss: float | None = None
    take_profit: list[float] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    # non-authoritative: passed through for logging/journal/review/operator display only
    # Risk Engine must not use this field for trade admissibility decisions
    invalidation: str | None = None
    reasoning_summary: str


class RiskReasonCode(str, Enum):
    RISK_OK = "RISK_OK"
    RISK_REJECTED = "RISK_REJECTED"
    DAILY_LIMIT_OK = "DAILY_LIMIT_OK"
    POSITIONS_OK = "POSITIONS_OK"
    DAILY_LIMIT_BREACHED = "DAILY_LIMIT_BREACHED"
    EXPOSURE_LIMIT_BREACHED = "EXPOSURE_LIMIT_BREACHED"
    DRAWDOWN_LOCK_ACTIVE = "DRAWDOWN_LOCK_ACTIVE"
    MAX_OPEN_POSITIONS_REACHED = "MAX_OPEN_POSITIONS_REACHED"
    KILL_SWITCH_REQUIRED = "KILL_SWITCH_REQUIRED"


class RiskDecision(BaseModel):
    risk_id: str
    signal_id: str
    symbol: str
    approved: bool
    position_size: float = 0.0
    notional_usdt: float = 0.0
    max_loss_usdt: float = 0.0
    risk_pct_of_equity: float = 0.0
    leverage: float = 0.0
    portfolio_exposure_pct: float = 0.0
    daily_loss_limit_status: str
    drawdown_lock: bool = False
    kill_switch_required: bool = False
    reason_codes: list[RiskReasonCode] = Field(default_factory=list)


class ExecutionCandidate(BaseModel):
    symbol: str
    side: OrderSide
    order_type: Literal["limit", "market"]
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: list[float] = Field(default_factory=list)
    time_in_force: str = "GTC"


class ReviewDecision(BaseModel):
    review_id: str
    signal_id: str
    risk_id: str
    passed: bool
    anomaly_flags: list[AnomalyFlag] = Field(default_factory=list)
    review_notes: str
    execution_candidate: ExecutionCandidate | None = None
