from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class JournalWriteResult(BaseModel):
    ok: bool
    event_id: str


class JournalQueryResult(BaseModel):
    ok: bool
    items: list[dict[str, Any]]
    total: int
