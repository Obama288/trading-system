from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.db.models.journal_event import JournalEventModel


class JournalReader:
    def __init__(self, db: Session) -> None:
        self.db = db

    def read_window(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        limit: int,
        event_type: str | None = None,
    ) -> list[dict]:
        stmt = (
            select(JournalEventModel)
            .where(JournalEventModel.created_at >= start_at)
            .where(JournalEventModel.created_at <= end_at)
            .order_by(JournalEventModel.created_at.asc(), JournalEventModel.event_id.asc())
            .limit(limit)
        )
        if event_type is not None:
            stmt = stmt.where(JournalEventModel.event_type == event_type)

        rows = self.db.execute(stmt).scalars().all()
        return [
            {
                "event_id": row.event_id,
                "event_type": row.event_type,
                "severity": row.severity,
                "correlation_id": row.correlation_id,
                "payload": row.payload,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
