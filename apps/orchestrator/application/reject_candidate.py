from __future__ import annotations

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.orchestrator.infrastructure.journal_client import JournalClient
from libs.db.repositories.operator_action_repo import OperatorActionRepository


def reject_candidate_use_case(
    repo: TradeCandidateRepository,
    operator_action_repo: OperatorActionRepository,
    journal_client: JournalClient,
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

    rejected = repo.reject_candidate(model, telegram_user_id=telegram_user_id)
    operator_action_repo.record(
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
    journal_client.write(
        {
            "event_id": f"evt_reject_{rejected.candidate_id}",
            "event_type": "candidate_rejected",
            "severity": "info",
            "correlation_id": correlation_id,
            "candidate_id": rejected.candidate_id,
            "payload": {"operator_user_id": telegram_user_id},
        }
    )
    return {"ok": True, "code": "REJECTED", "candidate_id": rejected.candidate_id}
