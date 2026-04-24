from __future__ import annotations

from apps.position_manager.infrastructure.journal_client import AlertClient, JournalClient
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionOpenRequest
from libs.schemas.common import ExecutionStatus, SeverityLevel


async def open_position_use_case(
    *,
    repo: PositionRepository,
    journal_client: JournalClient,
    alert_client: AlertClient,
    req: PositionOpenRequest,
) -> dict:
    if req.execution_status not in {ExecutionStatus.FILLED, ExecutionStatus.PARTIALLY_FILLED}:
        return {"ok": False, "code": "EXECUTION_NOT_FILLED"}

    existing = repo.get_by_execution_id(req.execution_id)
    if existing is not None:
        return {"ok": True, "code": "POSITION_EXISTS", "position": repo.to_dict(existing)}

    row = repo.create_position(
        execution_id=req.execution_id,
        symbol=req.symbol,
        side=req.side.value,
        quantity=req.quantity,
        entry_price=req.entry_price,
        opened_at=req.opened_at,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        ttl_expires_at=req.ttl_expires_at,
        candidate_id=req.candidate_id,
        signal_id=req.signal_id,
    )
    event_payload = {
        "position_id": row.position_id,
        "execution_id": row.execution_id,
        "symbol": row.symbol,
        "status": row.status,
        "quantity": row.quantity,
        "entry_price": row.entry_price,
    }
    repo.record_event(
        position_id=row.position_id,
        event_type="position_opened",
        correlation_id=req.correlation_id,
        payload=event_payload,
    )
    await journal_client.write(
        {
            "event_id": f"evt_position_opened_{row.position_id}",
            "event_type": "position_opened",
            "severity": SeverityLevel.INFO.value,
            "correlation_id": req.correlation_id,
            "payload": event_payload,
        }
    )
    await alert_client.notify(
        {
            "event_id": f"alert_position_opened_{row.position_id}",
            "event_type": "position_opened",
            "severity": SeverityLevel.INFO.value,
            "correlation_id": req.correlation_id,
            "payload": event_payload,
        }
    )
    return {"ok": True, "code": "POSITION_OPENED", "position": repo.to_dict(row)}
