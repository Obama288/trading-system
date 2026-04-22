from __future__ import annotations

from datetime import datetime, timezone

from apps.position_manager.domain.rules import evaluate_exit_rules
from apps.position_manager.infrastructure.journal_client import AlertClient, JournalClient
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import ExchangePositionSnapshot, PositionCloseRequest, ReconcileRequest
from libs.schemas.common import PositionCloseReason

from .close_position import close_position_use_case


def reconcile_positions_use_case(
    *,
    repo: PositionRepository,
    journal_client: JournalClient,
    alert_client: AlertClient,
    req: ReconcileRequest,
) -> dict:
    now = datetime.now(timezone.utc)
    snapshots = _index_snapshots(req.exchange_positions)
    reconciled: list[dict] = []

    for row in repo.list_open_positions():
        snapshot = snapshots.get(row.position_id) or snapshots.get(row.execution_id)
        if snapshot is None:
            result = close_position_use_case(
                repo=repo,
                journal_client=journal_client,
                alert_client=alert_client,
                req=PositionCloseRequest(
                    position_id=row.position_id,
                    reason=PositionCloseReason.RECONCILE,
                    close_price=None,
                    closed_at=now,
                    correlation_id=req.correlation_id,
                ),
            )
            reconciled.append(result)
            continue

        if snapshot.status.lower() in {"cancelled", "canceled"}:
            result = close_position_use_case(
                repo=repo,
                journal_client=journal_client,
                alert_client=alert_client,
                req=PositionCloseRequest(
                    position_id=row.position_id,
                    reason=PositionCloseReason.CANCELLED,
                    close_price=snapshot.mark_price,
                    closed_at=now,
                    correlation_id=req.correlation_id,
                ),
            )
            reconciled.append(result)
            continue

        if snapshot.status.lower() == "expired":
            result = close_position_use_case(
                repo=repo,
                journal_client=journal_client,
                alert_client=alert_client,
                req=PositionCloseRequest(
                    position_id=row.position_id,
                    reason=PositionCloseReason.EXPIRED,
                    close_price=snapshot.mark_price,
                    closed_at=now,
                    correlation_id=req.correlation_id,
                ),
            )
            reconciled.append(result)
            continue

        trigger = evaluate_exit_rules(repo.to_domain(row), snapshot.mark_price, now)
        if not trigger.should_close or trigger.reason is None:
            continue

        result = close_position_use_case(
            repo=repo,
            journal_client=journal_client,
            alert_client=alert_client,
            req=PositionCloseRequest(
                position_id=row.position_id,
                reason=trigger.reason,
                close_price=snapshot.mark_price,
                closed_at=now,
                correlation_id=req.correlation_id,
            ),
        )
        reconciled.append(result)

    return {
        "ok": True,
        "code": "RECONCILED",
        "reconciled_count": len(reconciled),
        "results": reconciled,
        "open_positions": [repo.to_dict(model) for model in repo.list_open_positions()],
    }


def _index_snapshots(exchange_positions: list[ExchangePositionSnapshot]) -> dict[str, ExchangePositionSnapshot]:
    indexed: dict[str, ExchangePositionSnapshot] = {}
    for snapshot in exchange_positions:
        if snapshot.position_id:
            indexed[snapshot.position_id] = snapshot
        if snapshot.execution_id:
            indexed[snapshot.execution_id] = snapshot
    return indexed
