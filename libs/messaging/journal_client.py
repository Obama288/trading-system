from __future__ import annotations

import asyncio
import os
from typing import Protocol

import httpx
from sqlalchemy.orm import Session

from libs.db.models.journal_event import JournalEventModel


class JournalClient(Protocol):
    async def write(self, payload: dict) -> None: ...


class HttpJournalClient:
    def __init__(
        self,
        base_url: str,
        retries: int = 2,
        retry_delay_seconds: float = 0.2,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds
        self.timeout_seconds = timeout_seconds
        self._token = os.getenv("INTERNAL_SERVICE_TOKEN")
        if not self._token:
            raise RuntimeError(
                "INTERNAL_SERVICE_TOKEN environment variable is not set. "
                "HttpJournalClient requires INTERNAL_SERVICE_TOKEN to call protected journal routes."
            )

    async def write(self, payload: dict) -> None:
        headers = {"X-Internal-Token": self._token}
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/journal/events",
                        json=payload,
                        headers=headers,
                    )
                response.raise_for_status()
                return
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    await asyncio.sleep(self.retry_delay_seconds)
        if last_error is None:
            raise RuntimeError("journal write failed without a captured exception")
        raise last_error


class DbJournalClient:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def write(self, payload: dict) -> None:
        row = JournalEventModel(
            event_id=payload["event_id"],
            event_type=payload["event_type"],
            severity=payload["severity"],
            correlation_id=payload["correlation_id"],
            payload=payload.get("payload", {}),
        )
        self.db.add(row)
        self.db.commit()
