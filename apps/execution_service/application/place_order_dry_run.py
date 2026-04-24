from __future__ import annotations

from uuid import uuid4

from apps.execution_service.domain.execution_policy import validate_execution_candidate
from apps.execution_service.domain.idempotency import validate_idempotency_key
from apps.execution_service.infrastructure.execution_store import ExecutionStore, StoredExecution
from libs.clients.kill_switch_client import KillSwitchClient, KillSwitchError
from libs.schemas.common import ExecutionCandidate


async def place_order_dry_run_use_case(
    *,
    candidate_id: str,
    execution_candidate: ExecutionCandidate,
    execution_idempotency_key: str,
    correlation_id: str,
    kill_switch_client: KillSwitchClient,
    store: ExecutionStore,
    execution_mode: str = "paper",
) -> dict:
    validate_idempotency_key(execution_idempotency_key)
    validate_execution_candidate(execution_candidate)

    existing = store.get_by_key(execution_idempotency_key)
    if existing is not None:
        return {
            "accepted": True,
            "duplicate": True,
            "execution_id": existing.execution_id,
            "candidate_id": existing.candidate_id,
            "status": existing.status,
            "mode": existing.mode,
            "payload": existing.payload,
        }

    try:
        ks = await kill_switch_client.get_status(correlation_id=correlation_id)
    except KillSwitchError:
        return {
            "accepted": False,
            "duplicate": False,
            "execution_id": None,
            "candidate_id": candidate_id,
            "status": "blocked",
            "mode": execution_mode,
            "payload": None,
            "error": {"code": "KILL_SWITCH_ACTIVE", "incident_code": "TRANSPORT_ERROR"},
        }
    ks_data = ks["data"]
    if not ks_data["trading_enabled"]:
        return {
            "accepted": False,
            "duplicate": False,
            "execution_id": None,
            "candidate_id": candidate_id,
            "status": "blocked",
            "mode": execution_mode,
            "payload": None,
            "error": {
                "code": "KILL_SWITCH_ACTIVE",
                "incident_code": ks_data["incident_code"],
            },
        }

    execution_id = f"exe_{uuid4().hex}"
    payload = {
        "symbol": execution_candidate.symbol,
        "side": execution_candidate.side.value,
        "order_type": execution_candidate.order_type,
        "entry_price": execution_candidate.entry_price,
        "quantity": execution_candidate.quantity,
        "stop_loss": execution_candidate.stop_loss,
        "take_profit": execution_candidate.take_profit,
        "time_in_force": execution_candidate.time_in_force,
    }

    stored = store.save(
        StoredExecution(
            execution_id=execution_id,
            idempotency_key=execution_idempotency_key,
            candidate_id=candidate_id,
            status="filled",
            mode=execution_mode,
            created_at=store.now_iso(),
            payload=payload,
        )
    )

    return {
        "accepted": True,
        "duplicate": False,
        "execution_id": stored.execution_id,
        "candidate_id": stored.candidate_id,
        "status": stored.status,
        "mode": stored.mode,
        "payload": stored.payload,
    }
