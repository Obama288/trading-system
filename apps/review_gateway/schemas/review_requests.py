from __future__ import annotations

from pydantic import BaseModel

from libs.schemas.common import MarketSnapshot, RiskDecision, SignalDecision


class ReviewCandidateRequest(BaseModel):
    signal: SignalDecision
    risk: RiskDecision
    market_snapshot: MarketSnapshot
    correlation_id: str
