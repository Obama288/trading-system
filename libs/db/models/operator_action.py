from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, JSON, String, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class OperatorActionModel(Base):
    __tablename__ = "operator_actions"

    action_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    operator_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[str] = mapped_column(String(128), index=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("NOW()"),
        index=True,
    )
