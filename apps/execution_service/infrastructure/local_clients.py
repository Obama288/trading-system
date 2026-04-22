from __future__ import annotations

from sqlalchemy.orm import Session

from libs.db.models.journal_event import JournalEventModel


class DbJournalClient:
    def __init__(self, db: Session) -> None:
        self.db = db

    def write(self, payload: dict) -> None:
        row = JournalEventModel(
            event_id=payload["event_id"],
            event_type=payload["event_type"],
            severity=payload["severity"],
            correlation_id=payload["correlation_id"],
            payload=payload.get("payload", {}),
        )
        self.db.add(row)
        self.db.commit()


class NoopAlertClient:
    def notify(self, payload: dict) -> None:
        return None
