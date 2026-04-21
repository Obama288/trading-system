from __future__ import annotations

from typing import Protocol

import httpx


class KillSwitchClient(Protocol):
    def get_status(self, correlation_id: str) -> dict: ...


class HttpKillSwitchClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def get_status(self, correlation_id: str) -> dict:
        response = httpx.get(
            f"{self.base_url}/v1/kill-switch/status",
            params={"correlation_id": correlation_id},
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json()


class StubKillSwitchClient:
    def __init__(self, trading_enabled: bool = True, incident_code: str | None = None) -> None:
        self.trading_enabled = trading_enabled
        self.incident_code = incident_code

    def get_status(self, correlation_id: str) -> dict:
        return {
            "ok": True,
            "service": "kill-switch",
            "version": "v1",
            "correlation_id": correlation_id,
            "data": {
                "trading_enabled": self.trading_enabled,
                "incident_code": self.incident_code,
            },
            "error": None,
        }
