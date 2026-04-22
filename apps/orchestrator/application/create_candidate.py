from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.orchestrator.infrastructure.journal_client import JournalClient
from libs.schemas.common import ReviewDecision, RiskDecision, SignalDecision

LOGGER = logging.getLogger(__name__)


def create_candidate_use_case(
    repo: TradeCandidateRepository,
    journal_client: JournalClient,
    signal: SignalDecision,
    risk: RiskDecision,
    review: ReviewDecision,
    correlation_id: str,
    ttl_seconds: int = 120,
) -> dict:
    if not review.passed or review.execution_candidate is None:
        return {"ok": False, "code": "REVIEW_NOT_EXECUTABLE"}
    if not risk.approved:
        return {"ok": False, "code": "RISK_NOT_APPROVED"}

    candidate_id = f"cand_{uuid4().hex}"
    ttl_expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    row = repo.create_candidate(
        candidate_id=candidate_id,
        signal_id=signal.signal_id,
        risk_id=risk.risk_id,
        review_id=review.review_id,
        symbol=signal.symbol,
        side=signal.side.value,
        execution_payload_json=review.execution_candidate.model_dump(mode="json"),
        ttl_expires_at=ttl_expires_at,
    )
    journal_write_ok = True
    journal_error: str | None = None
    try:
        journal_client.write(
            {
                "event_id": f"evt_candidate_{row.candidate_id}",
                "event_type": "candidate_created",
                "severity": "info",
                "correlation_id": correlation_id,
                "candidate_id": row.candidate_id,
                "signal_id": signal.signal_id,
                "risk_id": risk.risk_id,
                "review_id": review.review_id,
                "payload": {"status": row.status},
            }
        )
    except Exception as exc:
        journal_write_ok = False
        journal_error = str(exc)
        LOGGER.warning(
            "candidate_created journal write failed",
            extra={
                "candidate_id": row.candidate_id,
                "correlation_id": correlation_id,
                "journal_error": journal_error,
            },
        )
    return {
        "ok": True,
        "code": "CANDIDATE_CREATED",
        "candidate_id": row.candidate_id,
        "status": row.status,
        "ttl_expires_at": row.ttl_expires_at.isoformat(),
        "journal_write_ok": journal_write_ok,
        "journal_error": journal_error,
    }
