from __future__ import annotations

from apps.position_manager.infrastructure.journal_client import AlertClient, JournalClient
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionCloseRequest
from libs.schemas.common import PositionCloseReason, PositionStatus, SeverityLevel


def close_position_use_case(
    *,
    repo: PositionRepository,
    journal_client: JournalClient,
    alert_client: AlertClient,
    req: PositionCloseRequest,
) -> dict:
    model = repo.get_position(req.position_id)
    if model is None:
        return {"ok": False, "code": "NOT_FOUND"}
    if model.status != PositionStatus.OPEN.value:
        return {"ok": False, "code": "POSITION_NOT_OPEN", "position": repo.to_dict(model)}

    row = repo.close_position(
        model,
        reason=req.reason,
        closed_at=req.closed_at,
        close_price=req.close_price,
    )
    event_payload = {
        "position_id": row.position_id,
        "execution_id": row.execution_id,
        "status": row.status,
        "reason": row.close_reason,
        "close_price": row.close_price,
        "closed_at": row.closed_at.isoformat() if row.closed_at else None,
    }
    repo.record_event(
        position_id=row.position_id,
        event_type="position_closed",
        correlation_id=req.correlation_id,
        payload=event_payload,
    )
    severity = (
        SeverityLevel.WARNING.value
        if req.reason in {PositionCloseReason.STOP_LOSS, PositionCloseReason.EXPIRED, PositionCloseReason.RECONCILE}
        else SeverityLevel.INFO.value
    )
    journal_client.write(
        {
            "event_id": f"evt_position_closed_{row.position_id}",
            "event_type": "position_closed",
            "severity": severity,
            "correlation_id": req.correlation_id,
            "payload": event_payload,
        }
    )
    alert_client.notify(
        {
            "event_id": f"alert_position_closed_{row.position_id}",
            "event_type": "position_closed",
            "severity": severity,
            "correlation_id": req.correlation_id,
            "payload": event_payload,
        }
    )
    return {"ok": True, "code": "POSITION_CLOSED", "position": repo.to_dict(row)}
