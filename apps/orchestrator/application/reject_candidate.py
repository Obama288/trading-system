from __future__ import annotations

import logging
from sqlalchemy.exc import SQLAlchemyError

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from libs.db.models.journal_event import JournalEventModel
from libs.db.repositories.operator_action_repo import OperatorActionRepository

LOGGER = logging.getLogger(__name__)


def reject_candidate_use_case(
    repo: TradeCandidateRepository,
    operator_action_repo: OperatorActionRepository,
    candidate_id: str,
    telegram_user_id: int,
    correlation_id: str,
) -> dict:
    model = repo.get_candidate(candidate_id)
    if model is None:
        return {"ok": False, "code": "NOT_FOUND"}

    model = repo.expire_if_needed(model)
    if model.status == "expired":
        return {"ok": False, "code": "EXPIRED"}
    if model.status == "approved":
        return {"ok": False, "code": "ALREADY_APPROVED"}
    if model.status == "rejected":
        return {"ok": False, "code": "ALREADY_REJECTED"}

    try:
        rejected = repo.reject_candidate_no_commit(model, telegram_user_id=telegram_user_id)
        operator_action_repo.record_no_commit(
            operator_user_id=telegram_user_id,
            action_type="reject_candidate",
            target_type="trade_candidate",
            target_id=rejected.candidate_id,
            correlation_id=correlation_id,
            payload_json={
                "status": rejected.status,
                "candidate_id": rejected.candidate_id,
                "operator_user_id": telegram_user_id,
            },
        )
        repo.db.add(
            JournalEventModel(
                event_id=f"evt_reject_{rejected.candidate_id}",
                event_type="candidate_rejected",
                severity="info",
                correlation_id=correlation_id,
                payload={
                    "candidate_id": rejected.candidate_id,
                    "operator_user_id": telegram_user_id,
                },
            )
        )
        repo.db.flush()
        repo.db.commit()
        repo.db.refresh(rejected)
    except SQLAlchemyError as exc:
        repo.db.rollback()
        LOGGER.warning(
            "candidate_rejected journal DB write failed (rejection rolled back)",
            extra={"candidate_id": candidate_id, "correlation_id": correlation_id, "db_error": str(exc)},
        )
        return {"ok": False, "code": "JOURNAL_WRITE_FAILED"}

    return {"ok": True, "code": "REJECTED", "candidate_id": rejected.candidate_id}
