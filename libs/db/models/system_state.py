from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class SystemStateModel(Base):
    __tablename__ = "system_state"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[dict] = mapped_column(JSON, default=lambda: {})
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        index=True,
    )
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
