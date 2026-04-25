from __future__ import annotations

import logging
import httpx
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.orchestrator.infrastructure.execution_client import ExecutionClient
from libs.clients.kill_switch_client import (
    KillSwitchAuthError,
    KillSwitchClient,
    KillSwitchError,
    KillSwitchTimeoutError,
    KillSwitchUnavailableError,
)
from libs.db.models.journal_event import JournalEventModel
from libs.db.repositories.operator_action_repo import OperatorActionRepository

LOGGER = logging.getLogger(__name__)


async def approve_candidate_use_case(
    repo: TradeCandidateRepository,
    kill_switch_client: KillSwitchClient,
    execution_client: ExecutionClient,
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
    if model.status == "failed_execution":
        return {"ok": False, "code": "EXECUTION_FAILED"}
    if model.execution_payload_json is None:
        return {"ok": False, "code": "EXECUTION_PAYLOAD_MISSING"}
    try:
        kill_switch_status = await kill_switch_client.get_status(correlation_id=correlation_id)
    except (KillSwitchAuthError, KillSwitchTimeoutError, KillSwitchUnavailableError, KillSwitchError) as exc:
        if isinstance(exc, KillSwitchAuthError):
            error_code = "AUTH_FAILURE"
        elif isinstance(exc, KillSwitchTimeoutError):
            error_code = "KILL_SWITCH_TIMEOUT"
        elif isinstance(exc, KillSwitchUnavailableError):
            error_code = "KILL_SWITCH_UNAVAILABLE"
        else:
            error_code = "KILL_SWITCH_ERROR"
        LOGGER.warning(
            "kill_switch_check_failed",
            extra={"candidate_id": candidate_id, "correlation_id": correlation_id, "error_code": error_code, "error": str(exc)},
        )
        try:
            repo.db.add(JournalEventModel(
                event_id=f"evt_ks_error_{uuid4().hex}",
                event_type="kill_switch_check_failed",
                severity="error",
                correlation_id=correlation_id,
                payload={"candidate_id": candidate_id, "error_code": error_code, "detail": str(exc)},
            ))
            repo.db.flush()
            repo.db.commit()
        except SQLAlchemyError as db_exc:
            repo.db.rollback()
            LOGGER.warning(
                "kill_switch_check_failed journal write failed",
                extra={"candidate_id": candidate_id, "correlation_id": correlation_id, "db_error": str(db_exc)},
            )
        return {"ok": False, "code": error_code}

    if kill_switch_status.get("data", {}).get("kill_switch_active") is True:
        LOGGER.warning(
            "kill_switch_blocked",
            extra={"candidate_id": candidate_id, "correlation_id": correlation_id},
        )
        try:
            repo.db.add(JournalEventModel(
                event_id=f"evt_ks_blocked_{uuid4().hex}",
                event_type="kill_switch_blocked",
                severity="warning",
                correlation_id=correlation_id,
                payload={"candidate_id": candidate_id},
            ))
            repo.db.flush()
            repo.db.commit()
        except SQLAlchemyError as db_exc:
            repo.db.rollback()
            LOGGER.warning(
                "kill_switch_blocked journal write failed",
                extra={"candidate_id": candidate_id, "correlation_id": correlation_id, "db_error": str(db_exc)},
            )
        return {"ok": False, "code": "KILL_SWITCH_ACTIVE"}

    try:
        approved = repo.approve_candidate_no_commit(model, telegram_user_id=telegram_user_id)
        operator_action_repo.record_no_commit(
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
        repo.db.flush()
        repo.db.commit()
        repo.db.refresh(approved)
    except SQLAlchemyError as exc:
        repo.db.rollback()
        LOGGER.warning(
            "candidate approval DB write failed",
            extra={"candidate_id": candidate_id, "correlation_id": correlation_id, "db_error": str(exc)},
        )
        return {"ok": False, "code": "APPROVAL_PERSIST_FAILED"}

    try:
        execution_result = await execution_client.place(
            candidate_id=approved.candidate_id,
            execution_candidate=approved.execution_payload_json,
            correlation_id=correlation_id,
        )
    except httpx.HTTPError as exc:
        error_payload = {
            "code": "EXECUTION_REQUEST_FAILED",
            "message": str(exc),
        }
        try:
            repo.mark_execution_failed_no_commit(approved)
            repo.db.add(
                JournalEventModel(
                    event_id=f"evt_execution_failed_after_approval_{approved.candidate_id}",
                    event_type="execution_failed_after_approval",
                    severity="warning",
                    correlation_id=correlation_id,
                    payload={
                        "candidate_id": approved.candidate_id,
                        "operator_user_id": telegram_user_id,
                        "reason": "execution_request_failed",
                        "execution_error_code": "EXECUTION_REQUEST_FAILED",
                        "execution_error": error_payload,
                    },
                )
            )
            repo.db.flush()
            repo.db.commit()
            repo.db.refresh(approved)
        except SQLAlchemyError as db_exc:
            repo.db.rollback()
            LOGGER.warning(
                "execution_failed_after_approval journal DB write failed (status rolled back)",
                extra={"candidate_id": approved.candidate_id, "correlation_id": correlation_id, "db_error": str(db_exc)},
            )
            return {"ok": False, "code": "JOURNAL_WRITE_FAILED"}
        return {
            "ok": False,
            "code": "EXECUTION_REQUEST_FAILED",
            "candidate_id": approved.candidate_id,
            "execution_error_code": "EXECUTION_REQUEST_FAILED",
            "execution_error": error_payload,
        }
    except Exception as exc:
        error_payload = {
            "code": "EXECUTION_UNEXPECTED_ERROR",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
        try:
            repo.mark_execution_failed_no_commit(approved)
            repo.db.add(
                JournalEventModel(
                    event_id=f"evt_execution_failed_after_approval_{approved.candidate_id}",
                    event_type="execution_failed_after_approval",
                    severity="warning",
                    correlation_id=correlation_id,
                    payload={
                        "candidate_id": approved.candidate_id,
                        "operator_user_id": telegram_user_id,
                        "reason": "execution_unexpected_error",
                        "execution_error_code": "EXECUTION_UNEXPECTED_ERROR",
                        "execution_error": error_payload,
                    },
                )
            )
            repo.db.flush()
            repo.db.commit()
            repo.db.refresh(approved)
        except SQLAlchemyError as db_exc:
            repo.db.rollback()
            LOGGER.warning(
                "execution_failed_after_approval journal DB write failed (status rolled back)",
                extra={"candidate_id": approved.candidate_id, "correlation_id": correlation_id, "db_error": str(db_exc)},
            )
            return {"ok": False, "code": "JOURNAL_WRITE_FAILED"}
        return {
            "ok": False,
            "code": "EXECUTION_UNEXPECTED_ERROR",
            "candidate_id": approved.candidate_id,
            "execution_error_code": "EXECUTION_UNEXPECTED_ERROR",
            "execution_error": error_payload,
        }

    execution_id = execution_result.get("data", {}).get("execution_id") if execution_result.get("ok") else None
    if not execution_id:
        error_data = execution_result.get("error") or {}
        error_code = error_data.get("code") or "EXECUTION_SUBMISSION_NO_ID"
        failure_reason = "execution_submission_no_id" if execution_result.get("ok") else "execution_not_accepted"
        try:
            repo.mark_execution_failed_no_commit(approved)
            repo.db.add(
                JournalEventModel(
                    event_id=f"evt_execution_failed_after_approval_{approved.candidate_id}",
                    event_type="execution_failed_after_approval",
                    severity="warning",
                    correlation_id=correlation_id,
                    payload={
                        "candidate_id": approved.candidate_id,
                        "operator_user_id": telegram_user_id,
                        "reason": failure_reason,
                        "execution_error_code": error_code,
                        "execution_error": error_data,
                        "execution_result": execution_result,
                    },
                )
            )
            repo.db.flush()
            repo.db.commit()
            repo.db.refresh(approved)
        except SQLAlchemyError as db_exc:
            repo.db.rollback()
            LOGGER.warning(
                "execution_failed_after_approval journal DB write failed (status rolled back)",
                extra={"candidate_id": approved.candidate_id, "correlation_id": correlation_id, "db_error": str(db_exc)},
            )
            return {"ok": False, "code": "JOURNAL_WRITE_FAILED"}
        return {
            "ok": False,
            "code": error_code,
            "candidate_id": approved.candidate_id,
            "execution_error_code": error_code,
            "execution_error": error_data,
        }

    try:
        repo.attach_execution_no_commit(approved, execution_id)
        repo.db.add(
            JournalEventModel(
                event_id=f"evt_approve_{approved.candidate_id}",
                event_type="candidate_approved",
                severity="info",
                correlation_id=correlation_id,
                payload={
                    "candidate_id": approved.candidate_id,
                    "execution_id": execution_id,
                    "operator_user_id": telegram_user_id,
                },
            )
        )
        repo.db.flush()
        repo.db.commit()
        repo.db.refresh(approved)
    except SQLAlchemyError as exc:
        repo.db.rollback()
        LOGGER.warning(
            "candidate_approved journal DB write failed (submission rolled back)",
            extra={"candidate_id": approved.candidate_id, "correlation_id": correlation_id, "db_error": str(exc)},
        )
        return {"ok": False, "code": "JOURNAL_WRITE_FAILED"}

    return {
        "ok": True,
        "code": "APPROVED",
        "candidate_id": approved.candidate_id,
        "execution_id": execution_id,
    }
