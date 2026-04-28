from __future__ import annotations

from typing import Any

import httpx
from httpx import HTTPError

from libs.config.settings import BybitB1Settings
from libs.exchange.bybit_auth import BybitAuth
from libs.exchange.bybit_models import ServerTime
from libs.exchange.errors import (
    ExchangeAuthError,
    ExchangeConfigurationError,
    ExchangeRateLimited,
    ExchangeResponseError,
    MarketDataUnavailable,
)

_TESTNET_BASE_URL = "https://api-testnet.bybit.com"
_PRODUCTION_BASE_URLS = frozenset({
    "https://api.bybit.com",
    "https://api.bytick.com",
})
_ALLOWED_ENVIRONMENTS = frozenset({"testnet", "demo"})
_ALLOWED_PATHS = frozenset({"/v5/market/time"})
_AUTH_ERROR_CODES = frozenset({10003, 10004})
_RATE_LIMIT_CODE = 10006
_GENERIC_BYBIT_ERROR_REASON = "Bybit read-only request returned non-zero retCode"


class BybitReadOnlyClient:
    """Stage 53-B1 read-only Bybit client skeleton.

    Scope: testnet/demo server time connectivity only.
    No wallet balance, open positions, order status, orders, cancels, leverage,
    transfers, withdrawals, live reconcile, live execution, or service wiring.
    """

    def __init__(
        self,
        settings: BybitB1Settings,
        *,
        base_url: str | None = None,
        timeout: float = 10.0,
        recv_window_ms: int = 5_000,
    ) -> None:
        if settings.environment not in _ALLOWED_ENVIRONMENTS:
            raise ExchangeConfigurationError("Bybit B1 environment must be testnet or demo")
        if settings.api_key is None or settings.api_secret is None:
            raise ExchangeAuthError("Bybit B1 credentials are required")

        resolved_base_url = (base_url or _TESTNET_BASE_URL).rstrip("/")
        if resolved_base_url in _PRODUCTION_BASE_URLS:
            raise ExchangeConfigurationError("production Bybit base URL is forbidden")
        if "api.bybit.com" in resolved_base_url or "api.bytick.com" in resolved_base_url:
            raise ExchangeConfigurationError("production Bybit base URL is forbidden")

        self.settings = settings
        self.base_url = resolved_base_url
        self.timeout = timeout
        self._auth = BybitAuth(
            api_key=settings.api_key,
            api_secret=settings.api_secret,
            recv_window_ms=recv_window_ms,
        )

    def __repr__(self) -> str:
        return (
            "BybitReadOnlyClient("
            f"environment={self.settings.environment!r}, "
            f"base_url={self.base_url!r}, timeout={self.timeout!r})"
        )

    async def _signed_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if path not in _ALLOWED_PATHS:
            raise ExchangeConfigurationError(f"Bybit endpoint not allowed in B1 slice: {path}")

        url = f"{self.base_url}{path}"
        headers = self._auth.signed_headers(query_params=params)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params or {}, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except HTTPError as exc:
            raise MarketDataUnavailable(f"Bybit read-only request failed [{path}]") from exc

        _raise_for_bybit_error(payload)
        return payload

    async def get_server_time(self) -> ServerTime:
        payload = await self._signed_get("/v5/market/time")
        result = payload.get("result") or {}
        try:
            return ServerTime(
                exchange="bybit",
                time_second=int(result["timeSecond"]),
                time_nano=int(result["timeNano"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ExchangeResponseError(
                ret_code=0,
                ret_msg="Bybit server time payload missing required fields",
            ) from exc


def _raise_for_bybit_error(payload: dict[str, Any]) -> None:
    ret_code = int(payload.get("retCode", 0))
    if ret_code == 0:
        return
    if ret_code in _AUTH_ERROR_CODES:
        raise ExchangeAuthError(f"Bybit authentication failed (retCode {ret_code})")
    if ret_code == _RATE_LIMIT_CODE:
        raise ExchangeRateLimited(f"Bybit rate limited (retCode {ret_code})")
    raise ExchangeResponseError(
        ret_code=ret_code,
        ret_msg=f"{_GENERIC_BYBIT_ERROR_REASON}; endpoint_family=server_time",
    )
