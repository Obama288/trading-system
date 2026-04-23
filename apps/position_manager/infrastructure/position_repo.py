from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from apps.position_manager.domain.position import Position
from libs.db.models.execution import ExecutionModel
from libs.db.models.position import PositionModel
from libs.db.models.position_event import PositionEventModel
from libs.schemas.common import PositionCloseReason, PositionStatus, TradeDirection


class PositionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_execution_id(self, execution_id: str) -> PositionModel | None:
        stmt = select(PositionModel).where(PositionModel.execution_id == execution_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_position(self, position_id: str) -> PositionModel | None:
        stmt = select(PositionModel).where(PositionModel.position_id == position_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_open_positions(self) -> list[PositionModel]:
        stmt = (
            select(PositionModel)
            .where(PositionModel.status == PositionStatus.OPEN.value)
            .order_by(PositionModel.opened_at.desc(), PositionModel.position_id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def count_open_positions(self) -> int:
        stmt = select(func.count()).select_from(PositionModel).where(PositionModel.status == PositionStatus.OPEN.value)
        return int(self.db.execute(stmt).scalar_one())

    def count_pending_open_admissions(self, *, mode: str) -> int:
        # "Pending admission" = execution already created/filled but position row not created yet.
        # This closes the check-then-admit gap where concurrent admissions can overrun max_open_positions.
        stmt = (
            select(func.count())
            .select_from(ExecutionModel)
            .outerjoin(PositionModel, PositionModel.execution_id == ExecutionModel.execution_id)
            .where(ExecutionModel.mode == mode)
            .where(ExecutionModel.status == "filled")
            .where(PositionModel.execution_id.is_(None))
        )
        return int(self.db.execute(stmt).scalar_one())

    def acquire_open_position_admission_lock(self) -> None:
        # Transaction-scoped global lock for max-open admission checks.
        # Lock is released automatically when the current transaction commits/rolls back.
        dialect = self.db.bind.dialect.name if self.db.bind else ""
        if dialect != "postgresql":
            return  # advisory locks are PostgreSQL-only; skip on SQLite (tests)
        self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 5319001})

    def create_position(
        self,
        *,
        execution_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        opened_at: datetime,
        stop_loss: float | None,
        take_profit: list[float],
        ttl_expires_at: datetime | None,
        candidate_id: str | None,
        signal_id: str | None,
    ) -> PositionModel:
        model = PositionModel(
            position_id=f"pos_{uuid4().hex}",
            execution_id=execution_id,
            candidate_id=candidate_id,
            signal_id=signal_id,
            symbol=symbol,
            side=side,
            status=PositionStatus.OPEN.value,
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=opened_at,
            ttl_expires_at=ttl_expires_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def close_position(
        self,
        model: PositionModel,
        *,
        reason: PositionCloseReason,
        closed_at: datetime,
        close_price: float | None,
    ) -> PositionModel:
        status = (
            PositionStatus.CANCELLED
            if reason == PositionCloseReason.CANCELLED
            else PositionStatus.EXPIRED
            if reason == PositionCloseReason.EXPIRED
            else PositionStatus.CLOSED
        )
        model.status = status.value
        model.close_reason = reason.value
        model.closed_at = closed_at
        model.close_price = close_price
        model.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(model)
        return model

    def record_event(
        self,
        *,
        position_id: str,
        event_type: str,
        correlation_id: str,
        payload: dict,
    ) -> PositionEventModel:
        event = PositionEventModel(
            event_id=f"evt_pos_{uuid4().hex}",
            position_id=position_id,
            event_type=event_type,
            correlation_id=correlation_id,
            payload=payload,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    @staticmethod
    def to_domain(model: PositionModel) -> Position:
        return Position(
            position_id=model.position_id,
            execution_id=model.execution_id,
            symbol=model.symbol,
            side=TradeDirection(model.side),
            status=PositionStatus(model.status),
            quantity=model.quantity,
            entry_price=model.entry_price,
            stop_loss=model.stop_loss,
            take_profit=list(model.take_profit or []),
            opened_at=model.opened_at,
            ttl_expires_at=model.ttl_expires_at,
            candidate_id=model.candidate_id,
            signal_id=model.signal_id,
            closed_at=model.closed_at,
            close_price=model.close_price,
            close_reason=PositionCloseReason(model.close_reason) if model.close_reason else None,
        )

    @staticmethod
    def to_dict(model: PositionModel) -> dict:
        return {
            "position_id": model.position_id,
            "execution_id": model.execution_id,
            "candidate_id": model.candidate_id,
            "signal_id": model.signal_id,
            "symbol": model.symbol,
            "side": model.side,
            "status": model.status,
            "quantity": model.quantity,
            "entry_price": model.entry_price,
            "stop_loss": model.stop_loss,
            "take_profit": list(model.take_profit or []),
            "opened_at": model.opened_at.isoformat() if model.opened_at else None,
            "closed_at": model.closed_at.isoformat() if model.closed_at else None,
            "close_price": model.close_price,
            "close_reason": model.close_reason,
            "ttl_expires_at": model.ttl_expires_at.isoformat() if model.ttl_expires_at else None,
        }
