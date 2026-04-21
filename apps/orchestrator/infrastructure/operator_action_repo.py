from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from libs.db.models.operator_action import OperatorActionModel


class OperatorActionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        operator_user_id: int,
        action_type: str,
        target_type: str,
        target_id: str,
        correlation_id: str,
        payload_json: dict,
    ) -> OperatorActionModel:
        row = OperatorActionModel(
            action_id=f"op_{uuid4().hex}",
            operator_user_id=operator_user_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            correlation_id=correlation_id,
            payload_json=payload_json,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
