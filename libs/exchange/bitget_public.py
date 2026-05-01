from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from httpx import HTTPError

from libs.exchange.errors import ExchangeConfigurationError, ExchangeRateLimited, ExchangeResponseError, MarketDataUnavailable

_PUBLIC_BASE_URL = "https://api.bitget.com"
_SERVER_TIME_PATH = "/api/v2/public/time"
_SUCCESS_CODE = "00000"
_RATE_LIMIT_CODES = frozenset({"429", "42900"})


@dataclass(frozen=True)
class BitgetServerTime:
    """Sanitized Bitget public server time snapshot."""

    exchange: str
    server_time_ms: int

    @property
    def as_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.server_time_ms / 1000, tz=timezone.utc)


def _raise_for_bitget_error(payload: dict[str, Any]) -> None:
    code = str(payload.get("code", _SUCCESS_CODE))
    if code == _SUCCESS_CODE:
        return
    msg = str(payload.get("msg", ""))
    if code in _RATE_LIMIT_CODES:
        raise ExchangeRateLimited(f"Bitget public endpoint rate limited (code {code})")
    raise ExchangeResponseError(ret_code=0, ret_msg=f"Bitget public endpoint returned code {code}: {msg}")


class BitgetPublicClient:
    """Public-only Bitget connectivity skeleton.

    Scope: public unsigned endpoints only. No credentials, signing, passphrase,
    paptrading header, private endpoints, smoke scripts, or runtime wiring.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = (base_url or _PUBLIC_BASE_URL).rstrip("/")
        self.timeout = timeout

    def __repr__(self) -> str:
        return f"BitgetPublicClient(base_url={self.base_url!r}, timeout={self.timeout!r})"

    async def _public_get(self, path: str) -> dict[str, Any]:
        if path != _SERVER_TIME_PATH:
            raise ExchangeConfigurationError(f"Bitget public endpoint not allowed in BG2-A slice: {path}")

        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers={"User-Agent": "trading-system"})
                response.raise_for_status()
                payload = response.json()
        except HTTPError as exc:
            raise MarketDataUnavailable(f"Bitget public request failed [{path}]") from exc

        _raise_for_bitget_error(payload)
        return payload

    async def get_server_time(self) -> BitgetServerTime:
        payload = await self._public_get(_SERVER_TIME_PATH)
        data = payload.get("data") or {}
        try:
            server_time_ms = int(str(data.get("serverTime", payload["requestTime"])))
        except (KeyError, TypeError, ValueError) as exc:
            raise ExchangeResponseError(
                ret_code=0,
                ret_msg="Bitget public server time payload missing required fields",
            ) from exc
        return BitgetServerTime(exchange="bitget", server_time_ms=server_time_ms)
