from __future__ import annotations

import httpx

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.orchestrator.infrastructure.execution_client import ExecutionClient
from apps.orchestrator.infrastructure.journal_client import JournalClient
from libs.clients.kill_switch_client import KillSwitchClient
from libs.db.repositories.operator_action_repo import OperatorActionRepository


async def approve_candidate_use_case(
    repo: TradeCandidateRepository,
    kill_switch_client: KillSwitchClient,
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
    if model.status == "failed_execution":
        return {"ok": False, "code": "EXECUTION_FAILED"}
    if model.execution_payload_json is None:
        return {"ok": False, "code": "EXECUTION_PAYLOAD_MISSING"}
    kill_switch_status = await kill_switch_client.get_status(correlation_id=correlation_id)
    if kill_switch_status.get("data", {}).get("kill_switch_active") is True:
        return {"ok": False, "code": "KILL_SWITCH_ACTIVE"}

    approved = repo.approve_candidate(model, telegram_user_id=telegram_user_id)
    operator_action_repo.record(
        operator_user_id=telegram_user_id,
        action_type="approve_candidate",
        target_type="trade_candidate",
        target_id=approved.candidate_id,
        correlation_id=correlation_id,
        payload_json={
            "status": approved.status,
            "candidate_id": approved.candidate_id,
            "operator_user_id": telegram_user_id,
        },
    )

    try:
        execution_result = await execution_client.place(
            candidate_id=approved.candidate_id,
            execution_candidate=approved.execution_payload_json,
            correlation_id=correlation_id,
        )
    except httpx.HTTPError as exc:
        repo.mark_execution_failed(approved)
        error_payload = {
            "code": "EXECUTION_REQUEST_FAILED",
            "message": str(exc),
        }
        journal_client.write(
            {
                "event_id": f"evt_execution_failed_after_approval_{approved.candidate_id}",
                "event_type": "execution_failed_after_approval",
                "severity": "warning",
                "correlation_id": correlation_id,
                "candidate_id": approved.candidate_id,
                "payload": {
                    "operator_user_id": telegram_user_id,
                    "reason": "execution_request_failed",
                    "execution_error_code": "EXECUTION_REQUEST_FAILED",
                    "execution_error": error_payload,
                },
            }
        )
        return {
            "ok": False,
            "code": "EXECUTION_REQUEST_FAILED",
            "candidate_id": approved.candidate_id,
            "execution_error_code": "EXECUTION_REQUEST_FAILED",
            "execution_error": error_payload,
        }

    execution_id = execution_result.get("data", {}).get("execution_id") if execution_result.get("ok") else None
    if not execution_id:
        repo.mark_execution_failed(approved)
        error_data = execution_result.get("error") or {}
        error_code = error_data.get("code") or "EXECUTION_SUBMISSION_NO_ID"
        failure_reason = "execution_submission_no_id" if execution_result.get("ok") else "execution_not_accepted"
        journal_client.write(
            {
                "event_id": f"evt_execution_failed_after_approval_{approved.candidate_id}",
                "event_type": "execution_failed_after_approval",
                "severity": "warning",
                "correlation_id": correlation_id,
                "candidate_id": approved.candidate_id,
                "payload": {
                    "operator_user_id": telegram_user_id,
                    "reason": failure_reason,
                    "execution_error_code": error_code,
                    "execution_error": error_data,
                    "execution_result": execution_result,
                },
            }
        )
        return {
            "ok": False,
            "code": error_code,
            "candidate_id": approved.candidate_id,
            "execution_error_code": error_code,
            "execution_error": error_data,
        }

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
