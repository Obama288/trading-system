from __future__ import annotations

import os
from typing import Protocol

import httpx


class PositionManagerClient(Protocol):
    async def open_position(self, *, payload: dict, correlation_id: str) -> dict: ...


class HttpPositionManagerClient:
    def __init__(self, base_url: str, *, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._token = os.getenv("INTERNAL_SERVICE_TOKEN")
        if not self._token:
            raise RuntimeError(
                "INTERNAL_SERVICE_TOKEN environment variable is not set. "
                "HttpPositionManagerClient requires INTERNAL_SERVICE_TOKEN to call protected position-manager routes."
            )

    async def open_position(self, *, payload: dict, correlation_id: str) -> dict:
        headers = {"X-Correlation-Id": correlation_id, "X-Internal-Token": self._token}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/v1/positions/open",
                json=payload,
                headers=headers,
            )
        response.raise_for_status()
        return response.json()

