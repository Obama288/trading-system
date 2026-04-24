from __future__ import annotations

import os
from typing import Protocol

import httpx


class ExecutionClient(Protocol):
    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict: ...


class HttpExecutionClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = os.getenv("INTERNAL_SERVICE_TOKEN")
        if not self._token:
            raise RuntimeError(
                "INTERNAL_SERVICE_TOKEN environment variable is not set. "
                "HttpExecutionClient requires INTERNAL_SERVICE_TOKEN to call protected execution routes."
            )

    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict:
        payload = {
            "candidate_id": candidate_id,
            "execution_candidate": execution_candidate,
            "execution_idempotency_key": f"exec_{candidate_id}",
            "correlation_id": correlation_id,
        }
        headers = {"X-Internal-Token": self._token}
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{self.base_url}/v1/execution/place", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
