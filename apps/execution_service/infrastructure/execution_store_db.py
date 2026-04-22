from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.execution_service.infrastructure.execution_store import StoredExecution
from libs.db.models.execution import ExecutionModel


class DbExecutionStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_key(self, key: str) -> StoredExecution | None:
        stmt = select(ExecutionModel).where(ExecutionModel.idempotency_key == key)
        row = self.db.execute(stmt).scalar_one_or_none()
        return self._to_stored(row) if row is not None else None

    def get_by_execution_id(self, execution_id: str) -> StoredExecution | None:
        row = self.db.get(ExecutionModel, execution_id)
        return self._to_stored(row) if row is not None else None

    def save(self, execution: StoredExecution) -> StoredExecution:
        row = ExecutionModel(
            execution_id=execution.execution_id,
            idempotency_key=execution.idempotency_key,
            candidate_id=execution.candidate_id,
            status=execution.status,
            mode=execution.mode,
            payload=execution.payload,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_stored(row)

    def mark_cancelled(self, execution_id: str) -> StoredExecution | None:
        row = self.db.get(ExecutionModel, execution_id)
        if row is None:
            return None
        row.status = "cancelled"
        row.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(row)
        return self._to_stored(row)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _to_stored(row: ExecutionModel) -> StoredExecution:
        return StoredExecution(
            execution_id=row.execution_id,
            idempotency_key=row.idempotency_key,
            candidate_id=row.candidate_id,
            status=row.status,
            mode=row.mode,
            created_at=row.created_at.isoformat(),
            payload=row.payload,
        )
