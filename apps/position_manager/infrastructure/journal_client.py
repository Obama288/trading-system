from __future__ import annotations

import time
from typing import Protocol

import httpx

from libs.messaging.journal_client import HttpJournalClient, JournalClient


class AlertClient(Protocol):
    def notify(self, payload: dict) -> None: ...


class HttpAlertClient:
    def __init__(self, base_url: str, retries: int = 1, retry_delay_seconds: float = 0.2) -> None:
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    def notify(self, payload: dict) -> None:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = httpx.post(f"{self.base_url}/v1/alerts/events", json=payload, timeout=5.0)
                response.raise_for_status()
                return
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.retry_delay_seconds)
        if last_error is not None:
            raise last_error


class NoopAlertClient:
    def notify(self, payload: dict) -> None:
        return None


__all__ = [
    "AlertClient",
    "HttpAlertClient",
    "HttpJournalClient",
    "JournalClient",
    "NoopAlertClient",
]
