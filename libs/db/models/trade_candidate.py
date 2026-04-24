from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from libs.db.base import Base


class TradeCandidateModel(Base):
    __tablename__ = "trade_candidates"

    candidate_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    # signal_id is expected to be unique per signal evaluation. Enforce uniqueness to make
    # /v1/pipeline/evaluate idempotent on retries (TD-13).
    signal_id: Mapped[str] = mapped_column(String(128), index=True, unique=True)
    risk_id: Mapped[str] = mapped_column(String(128), index=True)
    review_id: Mapped[str] = mapped_column(String(128), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    side: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), index=True)
    execution_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ttl_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
