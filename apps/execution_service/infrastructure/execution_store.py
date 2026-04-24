from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass
class StoredExecution:
    execution_id: str
    idempotency_key: str
    candidate_id: str
    status: str
    mode: str
    created_at: str
    payload: dict


class ExecutionStore(Protocol):
    def get_by_key(self, key: str) -> StoredExecution | None: ...

    def get_by_execution_id(self, execution_id: str) -> StoredExecution | None: ...

    def save(self, execution: StoredExecution) -> StoredExecution: ...

    def mark_cancelled(self, execution_id: str) -> StoredExecution | None: ...

    def update_status(
        self,
        execution_id: str,
        *,
        status: str,
        payload_patch: dict | None = None,
    ) -> StoredExecution | None: ...

    @staticmethod
    def now_iso() -> str: ...


class InMemoryExecutionStore:
    # dry-run only store for MVP execution contour; replace with PostgreSQL-backed persistence before live use.
    def __init__(self) -> None:
        self.by_key: dict[str, StoredExecution] = {}
        self.by_execution_id: dict[str, StoredExecution] = {}

    def get_by_key(self, key: str) -> StoredExecution | None:
        return self.by_key.get(key)

    def get_by_execution_id(self, execution_id: str) -> StoredExecution | None:
        return self.by_execution_id.get(execution_id)

    def save(self, execution: StoredExecution) -> StoredExecution:
        self.by_key[execution.idempotency_key] = execution
        self.by_execution_id[execution.execution_id] = execution
        return execution

    def mark_cancelled(self, execution_id: str) -> StoredExecution | None:
        row = self.by_execution_id.get(execution_id)
        if row is None:
            return None
        row.status = "cancelled"
        return row

    def update_status(
        self,
        execution_id: str,
        *,
        status: str,
        payload_patch: dict | None = None,
    ) -> StoredExecution | None:
        row = self.by_execution_id.get(execution_id)
        if row is None:
            return None
        row.status = status
        if payload_patch:
            row.payload = {**(row.payload or {}), **payload_patch}
        return row

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
