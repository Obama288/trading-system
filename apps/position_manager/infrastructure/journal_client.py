from __future__ import annotations

import asyncio
import logging
import os
from typing import Protocol

import httpx

from libs.messaging.journal_client import HttpJournalClient, JournalClient

LOGGER = logging.getLogger(__name__)


class AlertClient(Protocol):
    async def notify(self, payload: dict) -> None: ...


class HttpAlertClient:
    def __init__(self, base_url: str, retries: int = 1, retry_delay_seconds: float = 0.2) -> None:
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds
        self._token = os.getenv("INTERNAL_SERVICE_TOKEN")
        if not self._token:
            raise RuntimeError(
                "INTERNAL_SERVICE_TOKEN environment variable is not set. "
                "HttpAlertClient requires INTERNAL_SERVICE_TOKEN to call protected alerts routes."
            )

    async def notify(self, payload: dict) -> None:
        headers = {"X-Internal-Token": self._token}
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(f"{self.base_url}/v1/alerts/events", json=payload, headers=headers)
                response.raise_for_status()
                return
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    await asyncio.sleep(self.retry_delay_seconds)
        if last_error is not None:
            LOGGER.warning(
                "alert notify failed (advisory — position state unaffected)",
                extra={"event_type": payload.get("event_type"), "error": str(last_error)},
            )


class NoopAlertClient:
    async def notify(self, payload: dict) -> None:
        return None


__all__ = [
    "AlertClient",
    "HttpAlertClient",
    "HttpJournalClient",
    "JournalClient",
    "NoopAlertClient",
]
