from __future__ import annotations

import os
from typing import Protocol

import httpx


class KillSwitchClient(Protocol):
    async def get_status(self, correlation_id: str) -> dict: ...


class HttpKillSwitchClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = os.getenv("INTERNAL_SERVICE_TOKEN")
        if not self._token:
            raise RuntimeError(
                "INTERNAL_SERVICE_TOKEN environment variable is not set. "
                "HttpKillSwitchClient requires INTERNAL_SERVICE_TOKEN to call protected kill-switch routes."
            )

    async def get_status(self, correlation_id: str) -> dict:
        headers = {"X-Internal-Token": self._token}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/kill-switch/status",
                    params={"correlation_id": correlation_id},
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return {
                "ok": False,
                "service": "kill-switch",
                "version": "v1",
                "correlation_id": correlation_id,
                "data": {
                    "trading_enabled": False,
                    "kill_switch_active": True,
                    "incident_code": "TRANSPORT_ERROR",
                },
                "error": {"code": "KILL_SWITCH_UNAVAILABLE", "detail": "Kill-switch unreachable or returned error, failing closed"},
            }


class StubKillSwitchClient:
    def __init__(self, trading_enabled: bool = True, incident_code: str | None = None) -> None:
        self.trading_enabled = trading_enabled
        self.incident_code = incident_code

    async def get_status(self, correlation_id: str) -> dict:
        return {
            "ok": True,
            "service": "kill-switch",
            "version": "v1",
            "correlation_id": correlation_id,
            "data": {
                "trading_enabled": self.trading_enabled,
                "kill_switch_active": not self.trading_enabled,
                "incident_code": self.incident_code,
            },
            "error": None,
        }
