from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class PaperAccountAuthorityModel(Base):
    __tablename__ = "paper_account_authority"

    account_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    equity_usdt: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        nullable=False,
    )
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
