from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.db.models.trade_candidate import TradeCandidateModel


class TradeCandidateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_candidate(
        self,
        *,
        candidate_id: str,
        signal_id: str,
        risk_id: str,
        review_id: str,
        symbol: str,
        side: str,
        execution_payload_json: dict,
        ttl_expires_at: datetime,
    ) -> TradeCandidateModel:
        model = TradeCandidateModel(
            candidate_id=candidate_id,
            signal_id=signal_id,
            risk_id=risk_id,
            review_id=review_id,
            symbol=symbol,
            side=side,
            status="pending",
            execution_payload_json=execution_payload_json,
            ttl_expires_at=ttl_expires_at,
        )
        self.db.add(model)
        # Commit/rollback is owned by the caller to allow atomic persistence with
        # other authoritative writes (e.g. journal_events).
        return model

    def attach_execution(self, model: TradeCandidateModel, execution_id: str) -> TradeCandidateModel:
        model.execution_id = execution_id
        model.status = "submitted"
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_candidate(self, candidate_id: str) -> TradeCandidateModel | None:
        stmt = select(TradeCandidateModel).where(TradeCandidateModel.candidate_id == candidate_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_signal_id(self, signal_id: str) -> TradeCandidateModel | None:
        stmt = select(TradeCandidateModel).where(TradeCandidateModel.signal_id == signal_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_pending(self) -> list[TradeCandidateModel]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(TradeCandidateModel)
            .where(TradeCandidateModel.status == "pending")
            .where(TradeCandidateModel.ttl_expires_at > now)
            .order_by(TradeCandidateModel.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def expire_if_needed(self, model: TradeCandidateModel) -> TradeCandidateModel:
        if model.status == "pending" and model.ttl_expires_at <= datetime.now(timezone.utc):
            model.status = "expired"
            self.db.commit()
            self.db.refresh(model)
        return model

    def approve_candidate(self, model: TradeCandidateModel, telegram_user_id: int) -> TradeCandidateModel:
        model.status = "approved"
        model.approved_by_user_id = telegram_user_id
        model.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(model)
        return model

    def mark_execution_failed(self, model: TradeCandidateModel) -> TradeCandidateModel:
        model.status = "failed_execution"
        model.execution_id = None
        self.db.commit()
        self.db.refresh(model)
        return model

    def reject_candidate(self, model: TradeCandidateModel, telegram_user_id: int) -> TradeCandidateModel:
        model.status = "rejected"
        model.rejected_by_user_id = telegram_user_id
        model.rejected_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(model)
        return model
