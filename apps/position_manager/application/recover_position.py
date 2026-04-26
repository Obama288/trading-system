from __future__ import annotations

import logging
from datetime import datetime, timezone

from apps.position_manager.infrastructure.journal_client import AlertClient, JournalClient
from apps.position_manager.infrastructure.position_repo import PositionRepository
from libs.schemas.common import ExecutionStatus, SeverityLevel, TradeDirection

LOGGER = logging.getLogger(__name__)


def _validate_recovery_payload(payload: dict) -> tuple[bool, list[str], list[str], str | None, float | None, float | None]:
    missing_fields: list[str] = []
    invalid_fields: list[str] = []
    symbol: str | None = None
    quantity: float | None = None
    entry_price: float | None = None

    for field in ("symbol", "quantity", "entry_price"):
        if field not in payload or payload[field] is None:
            missing_fields.append(field)

    if "symbol" not in missing_fields:
        raw_symbol = payload["symbol"]
        if not isinstance(raw_symbol, str) or raw_symbol == "":
            invalid_fields.append("symbol")
        else:
            symbol = raw_symbol

    if "quantity" not in missing_fields:
        try:
            quantity = float(payload["quantity"])
        except (TypeError, ValueError):
            invalid_fields.append("quantity")
        else:
            if quantity <= 0:
                invalid_fields.append("quantity")

    if "entry_price" not in missing_fields:
        try:
            entry_price = float(payload["entry_price"])
        except (TypeError, ValueError):
            invalid_fields.append("entry_price")
        else:
            if entry_price <= 0:
                invalid_fields.append("entry_price")

    return not missing_fields and not invalid_fields, missing_fields, invalid_fields, symbol, quantity, entry_price


async def recover_position_use_case(
    *,
    repo: PositionRepository,
    journal_client: JournalClient,
    alert_client: AlertClient,
    execution_id: str,
    correlation_id: str,
) -> dict:
    existing = repo.get_by_execution_id(execution_id)
    if existing is not None:
        return {"ok": True, "code": "POSITION_ALREADY_EXISTS", "position": repo.to_dict(existing)}

    exec_model = repo.get_execution_model(execution_id)
    if exec_model is None:
        return {"ok": False, "code": "EXECUTION_NOT_FOUND"}
    if exec_model.status != "filled":
        return {"ok": False, "code": "EXECUTION_NOT_FILLED", "status": exec_model.status}

    payload = exec_model.payload or {}
    valid_payload, missing_fields, invalid_fields, symbol, quantity, entry_price = _validate_recovery_payload(payload)
    if not valid_payload:
        return {
            "ok": False,
            "code": "EXECUTION_PAYLOAD_INVALID",
            "missing_fields": missing_fields,
            "invalid_fields": invalid_fields,
        }
    # position + position_event in one transaction — authoritative state before any HTTP side effects
    row = repo.create_position_no_commit(
        execution_id=execution_id,
        symbol=symbol,
        side=payload.get("side", "long"),
        quantity=quantity,
        entry_price=entry_price,
        opened_at=datetime.now(timezone.utc),
        stop_loss=payload.get("stop_loss"),
        take_profit=list(payload.get("take_profit") or []),
        ttl_expires_at=None,
        candidate_id=payload.get("candidate_id"),
        signal_id=payload.get("signal_id"),
    )
    event_payload = {
        "position_id": row.position_id,
        "execution_id": row.execution_id,
        "symbol": row.symbol,
        "status": row.status,
        "quantity": row.quantity,
        "entry_price": row.entry_price,
        "recovery": True,
    }
    repo.record_event_no_commit(
        position_id=row.position_id,
        event_type="position_recovered",
        correlation_id=correlation_id,
        payload=event_payload,
    )
    repo.db.commit()
    repo.db.refresh(row)

    # journal is audit visibility — failure must not roll back authoritative position state
    try:
        await journal_client.write(
            {
                "event_id": f"evt_position_recovered_{row.position_id}",
                "event_type": "position_recovered",
                "severity": SeverityLevel.INFO.value,
                "correlation_id": correlation_id,
                "payload": event_payload,
            }
        )
    except Exception as exc:
        LOGGER.warning(
            "position_recovered journal write failed (position committed — audit gap)",
            extra={"position_id": row.position_id, "execution_id": row.execution_id, "error": str(exc)},
        )

    try:
        await alert_client.notify(
            {
                "event_id": f"alert_position_recovered_{row.position_id}",
                "event_type": "position_recovered",
                "severity": SeverityLevel.INFO.value,
                "correlation_id": correlation_id,
                "payload": event_payload,
            }
        )
    except Exception as exc:
        LOGGER.warning(
            "position_recovered alert notify failed (advisory — position state unaffected)",
            extra={"position_id": row.position_id, "error": str(exc)},
        )

    return {"ok": True, "code": "POSITION_RECOVERED", "position": repo.to_dict(row)}
