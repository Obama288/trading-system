from __future__ import annotations

from apps.orchestrator.application.create_candidate import create_candidate_use_case
from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.orchestrator.infrastructure.journal_client import JournalClient
from libs.schemas.common import ReviewDecision, RiskDecision, SignalDecision


def evaluate_pipeline_use_case(
    repo: TradeCandidateRepository,
    journal_client: JournalClient,
    signal: SignalDecision,
    risk: RiskDecision,
    review: ReviewDecision,
    correlation_id: str,
) -> dict:
    return create_candidate_use_case(
        repo=repo,
        journal_client=journal_client,
        signal=signal,
        risk=risk,
        review=review,
        correlation_id=correlation_id,
    )
