from __future__ import annotations

from typing import Protocol

import httpx


class ExecutionClient(Protocol):
    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict: ...


class HttpExecutionClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict:
        payload = {
            "candidate_id": candidate_id,
            "execution_candidate": execution_candidate,
            "execution_idempotency_key": f"exec_{candidate_id}",
            "correlation_id": correlation_id,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{self.base_url}/v1/execution/place", json=payload)
            response.raise_for_status()
            return response.json()
