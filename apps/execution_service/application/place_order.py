from __future__ import annotations

from datetime import datetime, timezone

from apps.execution_service.application.place_order_dry_run import place_order_dry_run_use_case
from apps.execution_service.infrastructure.execution_store import ExecutionStore
from apps.execution_service.infrastructure.position_admission_repo import PositionAdmissionRepo
from apps.execution_service.infrastructure.position_manager_client import PositionManagerClient
from libs.clients.kill_switch_client import KillSwitchClient
from libs.config.settings import load_all_configs
from libs.schemas.common import ExecutionCandidate, ExecutionStatus, OrderSide, TradeDirection


def _order_side_to_trade_direction(side: OrderSide) -> TradeDirection:
    if side == OrderSide.BUY:
        return TradeDirection.LONG
    return TradeDirection.SHORT


def _duplicate_execution_result(existing) -> dict:
    return {
        "accepted": True,
        "duplicate": True,
        "execution_id": existing.execution_id,
        "candidate_id": existing.candidate_id,
        "status": existing.status,
        "mode": existing.mode,
        "payload": existing.payload,
        "error": None,
    }


def _max_open_positions_limit() -> int:
    return int(load_all_configs()["risk"]["risk"]["max_open_positions"])


async def place_order_use_case(
    *,
    candidate_id: str,
    execution_candidate: ExecutionCandidate,
    execution_idempotency_key: str,
    correlation_id: str,
    kill_switch_client: KillSwitchClient,
    store: ExecutionStore,
    admission_repo: PositionAdmissionRepo,
    position_manager_client: PositionManagerClient,
    journal_client,
    alert_client,
    execution_mode: str = "paper",
) -> dict:
    if execution_mode != "paper":
        raise ValueError(f"Unsupported execution mode: {execution_mode}")

    existing = store.get_by_key(execution_idempotency_key)
    if existing is not None:
        if existing.status == "position_opened":
            return _duplicate_execution_result(existing)
        if existing.status == "filled":
            # Recovery path: execution persisted but position may not have been opened due to a crash/timeout.
            # Position open is idempotent by execution_id in position-manager.
            side = (existing.payload or {}).get("side")
            trade_direction = TradeDirection.LONG if side == OrderSide.BUY.value else TradeDirection.SHORT
            open_payload = {
                "execution_id": existing.execution_id,
                "execution_status": ExecutionStatus.FILLED.value,
                "symbol": (existing.payload or {}).get("symbol"),
                "side": trade_direction.value,
                "quantity": float((existing.payload or {}).get("quantity")),
                "entry_price": float((existing.payload or {}).get("entry_price")),
                "stop_loss": (existing.payload or {}).get("stop_loss"),
                "take_profit": (existing.payload or {}).get("take_profit") or [],
                "opened_at": datetime.now(timezone.utc).isoformat(),
                "ttl_expires_at": None,
                "candidate_id": existing.candidate_id,
                "signal_id": None,
                "correlation_id": correlation_id,
            }
            try:
                pm_result = await position_manager_client.open_position(payload=open_payload, correlation_id=correlation_id)
                if pm_result.get("ok") is not True:
                    raise RuntimeError(f"position_manager returned ok=false: {pm_result}")
                store.update_status(existing.execution_id, status="position_opened")
                existing = store.get_by_key(execution_idempotency_key) or existing
                existing.status = "position_opened"
                return _duplicate_execution_result(existing)
            except Exception as exc:
                store.update_status(
                    existing.execution_id,
                    status="position_open_failed",
                    payload_patch={"position_open_error": {"message": str(exc), "service": "position-manager"}},
                )
                await journal_client.write(
                    {
                        "event_id": f"evt_position_open_failed_{existing.execution_id}",
                        "event_type": "position_open_failed",
                        "severity": "warning",
                        "correlation_id": correlation_id,
                        "payload": {
                            "candidate_id": existing.candidate_id,
                            "execution_id": existing.execution_id,
                            "symbol": (existing.payload or {}).get("symbol"),
                            "error": str(exc),
                        },
                    }
                )
                return {
                    "accepted": False,
                    "duplicate": True,
                    "execution_id": existing.execution_id,
                    "candidate_id": existing.candidate_id,
                    "status": "position_open_failed",
                    "mode": existing.mode,
                    "payload": existing.payload,
                    "error": {"code": "POSITION_OPEN_FAILED", "execution_id": existing.execution_id},
                }
        return {
            "accepted": False,
            "duplicate": True,
            "execution_id": existing.execution_id,
            "candidate_id": existing.candidate_id,
            "status": existing.status,
            "mode": existing.mode,
            "payload": existing.payload,
            "error": {"code": "EXECUTION_ALREADY_FAILED", "status": existing.status},
        }

    # Authoritative max-open gate at execution boundary (prevents stale pre-check over-admission).
    admission_repo.acquire_open_position_admission_lock()
    existing_after_lock = store.get_by_key(execution_idempotency_key)
    if existing_after_lock is not None:
        return _duplicate_execution_result(existing_after_lock)

    current_load = admission_repo.count_open_positions() + admission_repo.count_pending_open_admissions(mode=execution_mode)
    max_open_positions = _max_open_positions_limit()
    if current_load >= max_open_positions:
        return {
            "accepted": False,
            "duplicate": False,
            "execution_id": None,
            "candidate_id": candidate_id,
            "status": "blocked",
            "mode": execution_mode,
            "payload": None,
            "error": {
                "code": "MAX_OPEN_POSITIONS_REACHED",
                "max_open_positions": max_open_positions,
                "current_load": current_load,
            },
        }

    result = await place_order_dry_run_use_case(
        candidate_id=candidate_id,
        execution_candidate=execution_candidate,
        execution_idempotency_key=execution_idempotency_key,
        correlation_id=correlation_id,
        kill_switch_client=kill_switch_client,
        store=store,
        execution_mode=execution_mode,
    )
    if not result["accepted"]:
        return result

    if not result.get("duplicate"):
        await journal_client.write(
            {
                "event_id": f"evt_paper_execution_filled_{result['execution_id']}",
                "event_type": "paper_execution_filled",
                "severity": "info",
                "correlation_id": correlation_id,
                "payload": {
                    "execution_id": result["execution_id"],
                    "symbol": execution_candidate.symbol,
                    "side": execution_candidate.side.value,
                    "price": execution_candidate.entry_price,
                    "quantity": execution_candidate.quantity,
                    "correlation_id": correlation_id,
                },
            }
        )

    open_payload = {
        "execution_id": result["execution_id"],
        "execution_status": ExecutionStatus.FILLED.value,
        "symbol": execution_candidate.symbol,
        "side": _order_side_to_trade_direction(execution_candidate.side).value,
        "quantity": float(execution_candidate.quantity),
        "entry_price": float(execution_candidate.entry_price),
        "stop_loss": float(execution_candidate.stop_loss) if execution_candidate.stop_loss is not None else None,
        "take_profit": [float(x) for x in (execution_candidate.take_profit or [])],
        "opened_at": datetime.now(timezone.utc).isoformat(),
        "ttl_expires_at": None,
        "candidate_id": candidate_id,
        "signal_id": None,
        "correlation_id": correlation_id,
    }

    try:
        pm_result = await position_manager_client.open_position(payload=open_payload, correlation_id=correlation_id)
        if pm_result.get("ok") is not True:
            raise RuntimeError(f"position_manager returned ok=false: {pm_result}")
        store.update_status(result["execution_id"], status="position_opened")
        result["status"] = "position_opened"
    except Exception as exc:
        store.update_status(
            result["execution_id"],
            status="position_open_failed",
            payload_patch={"position_open_error": {"message": str(exc), "service": "position-manager"}},
        )
        await journal_client.write(
            {
                "event_id": f"evt_position_open_failed_{result['execution_id']}",
                "event_type": "position_open_failed",
                "severity": "warning",
                "correlation_id": correlation_id,
                "payload": {
                    "candidate_id": candidate_id,
                    "execution_id": result["execution_id"],
                    "symbol": execution_candidate.symbol,
                    "error": str(exc),
                },
            }
        )
        return {
            "accepted": False,
            "duplicate": False,
            "execution_id": result["execution_id"],
            "candidate_id": candidate_id,
            "status": "position_open_failed",
            "mode": execution_mode,
            "payload": result.get("payload"),
            "error": {"code": "POSITION_OPEN_FAILED", "execution_id": result["execution_id"]},
        }

    return result
