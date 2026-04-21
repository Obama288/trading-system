from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class JournalEventModel(Base):
    __tablename__ = "journal_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        index=True,
    )
