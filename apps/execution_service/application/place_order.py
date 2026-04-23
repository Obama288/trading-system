from __future__ import annotations

from datetime import datetime, timezone

from apps.execution_service.application.place_order_dry_run import place_order_dry_run_use_case
from apps.execution_service.infrastructure.execution_store import ExecutionStore
from apps.position_manager.application.open_position import open_position_use_case
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionOpenRequest
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
    position_repo: PositionRepository,
    journal_client,
    alert_client,
    execution_mode: str = "paper",
) -> dict:
    if execution_mode != "paper":
        raise ValueError(f"Unsupported execution mode: {execution_mode}")

    existing = store.get_by_key(execution_idempotency_key)
    if existing is not None:
        return _duplicate_execution_result(existing)

    # Authoritative max-open gate at execution boundary (prevents stale pre-check over-admission).
    position_repo.acquire_open_position_admission_lock()
    existing_after_lock = store.get_by_key(execution_idempotency_key)
    if existing_after_lock is not None:
        return _duplicate_execution_result(existing_after_lock)

    current_load = position_repo.count_open_positions() + position_repo.count_pending_open_admissions(mode=execution_mode)
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
        journal_client.write(
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

    open_position_use_case(
        repo=position_repo,
        journal_client=journal_client,
        alert_client=alert_client,
        req=PositionOpenRequest(
            execution_id=result["execution_id"],
            execution_status=ExecutionStatus.FILLED,
            symbol=execution_candidate.symbol,
            side=_order_side_to_trade_direction(execution_candidate.side),
            quantity=execution_candidate.quantity,
            entry_price=execution_candidate.entry_price,
            stop_loss=execution_candidate.stop_loss,
            take_profit=execution_candidate.take_profit,
            opened_at=datetime.now(timezone.utc),
            ttl_expires_at=None,
            candidate_id=candidate_id,
            signal_id=None,
            correlation_id=correlation_id,
        ),
    )

    return result
