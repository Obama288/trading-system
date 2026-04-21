from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from libs.schemas.common import SeverityLevel


class JournalEventRequest(BaseModel):
    event_id: str
    event_type: str
    severity: SeverityLevel
    correlation_id: str
    payload: dict[str, Any] = {}


class JournalQueryRequest(BaseModel):
    event_type: str | None = None
    correlation_id: str | None = None
    limit: int = 50
    offset: int = 0
