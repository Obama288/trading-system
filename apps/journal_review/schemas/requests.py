from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DailySummaryRequest(BaseModel):
    start_at: datetime
    end_at: datetime
    limit: int = Field(default=200, ge=1, le=1000)
    correlation_id: str


class PatternReviewRequest(BaseModel):
    start_at: datetime
    end_at: datetime
    event_type: str | None = None
    limit: int = Field(default=500, ge=1, le=2000)
    correlation_id: str
