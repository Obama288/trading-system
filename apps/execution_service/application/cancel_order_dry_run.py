from __future__ import annotations

from apps.execution_service.infrastructure.execution_store import ExecutionStore


def cancel_order_dry_run_use_case(
    *,
    execution_id: str,
    store: ExecutionStore,
) -> dict:
    row = store.mark_cancelled(execution_id)
    if row is None:
        return {
            "ok": False,
            "execution_id": execution_id,
            "status": "not_found",
        }

    return {
        "ok": True,
        "execution_id": execution_id,
        "status": row.status,
        "mode": row.mode,
    }
