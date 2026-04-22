from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class PositionEventModel(Base):
    __tablename__ = "position_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    position_id: Mapped[str] = mapped_column(String(128), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        index=True,
    )
