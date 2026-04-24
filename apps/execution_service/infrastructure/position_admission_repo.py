from __future__ import annotations

from typing import Protocol

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from libs.db.models.execution import ExecutionModel
from libs.db.models.position import PositionModel


class PositionAdmissionRepo(Protocol):
    def acquire_open_position_admission_lock(self) -> None: ...

    def count_open_positions(self) -> int: ...

    def count_pending_open_admissions(self, *, mode: str) -> int: ...


class DbPositionAdmissionRepo:
    """
    DB-backed admission gate support for execution-service.

    This intentionally lives in execution_service/infrastructure (not apps/position_manager) to
    avoid cross-service imports while still reading authoritative tables.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def acquire_open_position_admission_lock(self) -> None:
        # Transaction-scoped global lock for max-open admission checks.
        dialect = self.db.bind.dialect.name if self.db.bind else ""
        if dialect != "postgresql":
            return  # advisory locks are PostgreSQL-only; skip on SQLite (tests)
        self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 5319001})

    def count_open_positions(self) -> int:
        stmt = select(func.count()).select_from(PositionModel).where(PositionModel.status == "open")
        return int(self.db.execute(stmt).scalar_one())

    def count_pending_open_admissions(self, *, mode: str) -> int:
        # "Pending admission" = execution already filled but position row not created yet.
        stmt = (
            select(func.count())
            .select_from(ExecutionModel)
            .outerjoin(PositionModel, PositionModel.execution_id == ExecutionModel.execution_id)
            .where(ExecutionModel.mode == mode)
            .where(ExecutionModel.status == "filled")
            .where(PositionModel.execution_id.is_(None))
        )
        return int(self.db.execute(stmt).scalar_one())

    def get_pending_open_executions(self, *, mode: str | None = None) -> list[ExecutionModel]:
        # "Pending open" = executions with status="filled" that have no corresponding position.
        # Returns executions that may be orphaned (filled without position) - for detection only.
        stmt = (
            select(ExecutionModel)
            .outerjoin(PositionModel, PositionModel.execution_id == ExecutionModel.execution_id)
            .where(ExecutionModel.status == "filled")
            .where(PositionModel.execution_id.is_(None))
        )
        if mode is not None:
            stmt = stmt.where(ExecutionModel.mode == mode)
        return list(self.db.execute(stmt).scalars().all())
