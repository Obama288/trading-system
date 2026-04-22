from __future__ import annotations

import time
from typing import Protocol

import httpx


class JournalClient(Protocol):
    def write(self, payload: dict) -> None: ...


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

    def write(self, payload: dict) -> None:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = httpx.post(
                    f"{self.base_url}/v1/journal/events",
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.retry_delay_seconds)
        if last_error is None:
            raise RuntimeError("journal write failed without a captured exception")
        raise last_error
