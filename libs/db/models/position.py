from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, JSON, String, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class PositionModel(Base):
    __tablename__ = "positions"

    position_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    candidate_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    signal_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    side: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[list[float]] = mapped_column(JSON, default=list)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ttl_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
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
