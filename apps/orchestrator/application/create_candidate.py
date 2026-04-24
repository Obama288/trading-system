from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from libs.db.models.journal_event import JournalEventModel
from libs.schemas.common import ReviewDecision, RiskDecision, SignalDecision

LOGGER = logging.getLogger(__name__)


class _JournalWriteFailed(RuntimeError):
    pass


class _CandidateAlreadyExists(RuntimeError):
    pass


def create_candidate_use_case(
    repo: TradeCandidateRepository,
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

    # TD-13: make evaluate idempotent on retries by de-duplicating on signal_id.
    existing = repo.get_by_signal_id(signal.signal_id)
    if existing is not None:
        if existing.risk_id != risk.risk_id or existing.review_id != review.review_id:
            return {"ok": False, "code": "SIGNAL_ID_REUSE_CONFLICT"}
        return {
            "ok": True,
            "code": "CANDIDATE_EXISTS",
            "candidate_id": existing.candidate_id,
            "status": existing.status,
            "ttl_expires_at": existing.ttl_expires_at.isoformat(),
        }

    candidate_id = f"cand_{uuid4().hex}"
    ttl_expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    try:
        # TD-12 hardening: make candidate persistence and candidate_created journaling atomic.
        # If we cannot record the journal event, we must not persist the candidate.
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
        try:
            repo.db.flush()
        except IntegrityError as exc:
            # Another request created the candidate concurrently. Session is now in failed state.
            repo.db.rollback()
            raise _CandidateAlreadyExists() from exc

        event = JournalEventModel(
            event_id=f"evt_candidate_{row.candidate_id}",
            event_type="candidate_created",
            severity="info",
            correlation_id=correlation_id,
            payload={
                "candidate_id": row.candidate_id,
                "signal_id": signal.signal_id,
                "risk_id": risk.risk_id,
                "review_id": review.review_id,
                "status": row.status,
            },
        )
        repo.db.add(event)
        try:
            # Force the INSERT now so we can reliably classify journal write failures.
            repo.db.flush()
        except SQLAlchemyError as exc:
            repo.db.rollback()
            raise _JournalWriteFailed(str(exc)) from exc

        repo.db.commit()
    except _CandidateAlreadyExists:
        existing = repo.get_by_signal_id(signal.signal_id)
        if existing is None:
            return {"ok": False, "code": "CANDIDATE_PERSIST_FAILED"}
        if existing.risk_id != risk.risk_id or existing.review_id != review.review_id:
            return {"ok": False, "code": "SIGNAL_ID_REUSE_CONFLICT"}
        return {
            "ok": True,
            "code": "CANDIDATE_EXISTS",
            "candidate_id": existing.candidate_id,
            "status": existing.status,
            "ttl_expires_at": existing.ttl_expires_at.isoformat(),
        }
    except _JournalWriteFailed as exc:
        LOGGER.warning(
            "candidate_created journal DB write failed (candidate rolled back)",
            extra={"candidate_id": candidate_id, "correlation_id": correlation_id, "journal_error": str(exc)},
        )
        return {"ok": False, "code": "JOURNAL_WRITE_FAILED"}
    except Exception as exc:
        repo.db.rollback()
        LOGGER.exception(
            "candidate persistence failed",
            extra={"candidate_id": candidate_id, "correlation_id": correlation_id, "error": str(exc)},
        )
        return {"ok": False, "code": "CANDIDATE_PERSIST_FAILED"}

    return {
        "ok": True,
        "code": "CANDIDATE_CREATED",
        "candidate_id": candidate_id,
        "status": "pending",
        "ttl_expires_at": ttl_expires_at.isoformat(),
    }
