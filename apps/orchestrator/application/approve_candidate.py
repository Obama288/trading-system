from __future__ import annotations

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.orchestrator.infrastructure.execution_client import ExecutionClient
from apps.orchestrator.infrastructure.journal_client import JournalClient
from apps.orchestrator.infrastructure.operator_action_repo import OperatorActionRepository


def approve_candidate_use_case(
    repo: TradeCandidateRepository,
    execution_client: ExecutionClient,
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
    if model.execution_payload_json is None:
        return {"ok": False, "code": "EXECUTION_PAYLOAD_MISSING"}

    approved = repo.approve_candidate(model, telegram_user_id=telegram_user_id)
    operator_action_repo.record(
        operator_user_id=telegram_user_id,
        action_type="approve_candidate",
        target_type="trade_candidate",
        target_id=approved.candidate_id,
        correlation_id=correlation_id,
        payload_json={"status": approved.status},
    )

    execution_result = execution_client.place(
        candidate_id=approved.candidate_id,
        execution_candidate=approved.execution_payload_json,
        correlation_id=correlation_id,
    )

    execution_id = execution_result.get("data", {}).get("execution_id")
    if not execution_id:
        journal_client.write(
            {
                "event_id": f"evt_approve_no_execution_id_{approved.candidate_id}",
                "event_type": "candidate_approve_handoff_failed",
                "severity": "warning",
                "correlation_id": correlation_id,
                "candidate_id": approved.candidate_id,
                "payload": {
                    "operator_user_id": telegram_user_id,
                    "reason": "execution_submission_no_id",
                    "execution_result": execution_result,
                },
            }
        )
        return {"ok": False, "code": "EXECUTION_SUBMISSION_NO_ID", "candidate_id": approved.candidate_id}

    repo.attach_execution(approved, execution_id)
    journal_client.write(
        {
            "event_id": f"evt_approve_{approved.candidate_id}",
            "event_type": "candidate_approved",
            "severity": "info",
            "correlation_id": correlation_id,
            "candidate_id": approved.candidate_id,
            "execution_id": execution_id,
            "payload": {"operator_user_id": telegram_user_id},
        }
    )

    return {
        "ok": True,
        "code": "APPROVED",
        "candidate_id": approved.candidate_id,
        "execution_id": execution_id,
    }
