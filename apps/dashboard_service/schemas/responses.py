from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    kill_switch_active: bool
    pending_candidates_count: int
    open_positions_count: int
    recent_incidents_count: int
    recent_journal_events_count: int


class StatsBucketResponse(BaseModel):
    total_trades: int
    win_rate_pct: float
    avg_rr: float
    total_pnl_usdt: float
    avg_hold_candles: float


class DashboardStatsResponse(BaseModel):
    total_trades: int
    win_rate_pct: float
    avg_rr: float
    total_pnl_usdt: float
    avg_hold_candles: float
    by_symbol: dict[str, StatsBucketResponse]
    by_setup_type: dict[str, StatsBucketResponse]


class CandidateItem(BaseModel):
    candidate_id: str
    signal_id: str
    risk_id: str
    review_id: str
    symbol: str
    side: str
    status: str
    execution_payload_json: dict[str, Any] | None = None
    ttl_expires_at: str | None = None
    approved_by_user_id: int | None = None
    approved_at: str | None = None
    rejected_by_user_id: int | None = None
    rejected_at: str | None = None
    execution_id: str | None = None
    created_at: str | None = None


class PositionItem(BaseModel):
    position_id: str
    execution_id: str
    candidate_id: str | None = None
    signal_id: str | None = None
    symbol: str
    side: str
    status: str
    quantity: float
    entry_price: float
    stop_loss: float | None = None
    take_profit: list[float] = Field(default_factory=list)
    opened_at: str | None = None
    closed_at: str | None = None
    close_price: float | None = None
    close_reason: str | None = None
    ttl_expires_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class IncidentItem(BaseModel):
    incident_id: str
    incident_type: str
    severity: str
    source_service: str
    message: str
    correlation_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
