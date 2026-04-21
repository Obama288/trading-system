from __future__ import annotations

from pydantic import BaseModel

from libs.schemas.common import ReviewDecision, RiskDecision, SignalDecision


class EvaluatePipelineRequest(BaseModel):
    signal: SignalDecision
    risk: RiskDecision
    review: ReviewDecision
    correlation_id: str


class ApproveCandidateRequest(BaseModel):
    candidate_id: str
    telegram_user_id: int
    correlation_id: str


class RejectCandidateRequest(BaseModel):
    candidate_id: str
    telegram_user_id: int
    correlation_id: str
