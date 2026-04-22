from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from libs.db.models.incident import IncidentModel
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.position import PositionModel
from libs.db.models.system_state import SystemStateModel
from libs.db.models.trade_candidate import TradeCandidateModel
from libs.schemas.common import PositionStatus


class DashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self) -> dict:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)

        kill_switch_row = self.db.execute(
            select(SystemStateModel).where(SystemStateModel.key == "kill_switch_state")
        ).scalar_one_or_none()
        kill_switch_active = True if kill_switch_row is None else bool(kill_switch_row.value_json.get("kill_switch_active", True))

        pending_candidates_count = self.db.execute(
            select(func.count()).select_from(TradeCandidateModel).where(TradeCandidateModel.status == "pending")
        ).scalar_one()
        open_positions_count = self.db.execute(
            select(func.count()).select_from(PositionModel).where(PositionModel.status == PositionStatus.OPEN.value)
        ).scalar_one()
        recent_incidents_count = self.db.execute(
            select(func.count()).select_from(IncidentModel).where(IncidentModel.created_at >= cutoff)
        ).scalar_one()
        recent_journal_events_count = self.db.execute(
            select(func.count()).select_from(JournalEventModel).where(JournalEventModel.created_at >= cutoff)
        ).scalar_one()

        return {
            "kill_switch_active": kill_switch_active,
            "pending_candidates_count": pending_candidates_count,
            "open_positions_count": open_positions_count,
            "recent_incidents_count": recent_incidents_count,
            "recent_journal_events_count": recent_journal_events_count,
        }

    def list_candidates(self) -> list[dict]:
        stmt = select(TradeCandidateModel).order_by(
            TradeCandidateModel.created_at.desc(),
            TradeCandidateModel.candidate_id.desc(),
        )
        rows = self.db.execute(stmt).scalars().all()
        return [self._candidate_to_dict(row) for row in rows]

    def list_open_positions(self) -> list[dict]:
        stmt = (
            select(PositionModel)
            .where(PositionModel.status == PositionStatus.OPEN.value)
            .order_by(PositionModel.opened_at.desc(), PositionModel.position_id.desc())
        )
        rows = self.db.execute(stmt).scalars().all()
        return [self._position_to_dict(row) for row in rows]

    def list_incidents(self, *, limit: int = 50) -> list[dict]:
        safe_limit = max(1, min(limit, 50))
        stmt = (
            select(IncidentModel)
            .order_by(IncidentModel.created_at.desc(), IncidentModel.incident_id.desc())
            .limit(safe_limit)
        )
        rows = self.db.execute(stmt).scalars().all()
        return [self._incident_to_dict(row) for row in rows]

    @staticmethod
    def _candidate_to_dict(model: TradeCandidateModel) -> dict:
        return {
            "candidate_id": model.candidate_id,
            "signal_id": model.signal_id,
            "risk_id": model.risk_id,
            "review_id": model.review_id,
            "symbol": model.symbol,
            "side": model.side,
            "status": model.status,
            "execution_payload_json": model.execution_payload_json,
            "ttl_expires_at": model.ttl_expires_at.isoformat() if model.ttl_expires_at else None,
            "approved_by_user_id": model.approved_by_user_id,
            "approved_at": model.approved_at.isoformat() if model.approved_at else None,
            "rejected_by_user_id": model.rejected_by_user_id,
            "rejected_at": model.rejected_at.isoformat() if model.rejected_at else None,
            "execution_id": model.execution_id,
            "created_at": model.created_at.isoformat() if model.created_at else None,
        }

    @staticmethod
    def _position_to_dict(model: PositionModel) -> dict:
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
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    @staticmethod
    def _incident_to_dict(model: IncidentModel) -> dict:
        return {
            "incident_id": model.incident_id,
            "incident_type": model.incident_type,
            "severity": model.severity,
            "source_service": model.source_service,
            "message": model.message,
            "correlation_id": model.correlation_id,
            "payload": model.payload,
            "created_at": model.created_at.isoformat() if model.created_at else None,
        }
