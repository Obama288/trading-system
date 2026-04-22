from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class ExecutionModel(Base):
    __tablename__ = "executions"

    execution_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    mode: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
    )
