from __future__ import annotations

from decimal import Decimal, DecimalException
from typing import Any

import httpx
from httpx import HTTPError

from libs.config.settings import BybitB1Settings
from libs.exchange.bybit_auth import BybitAuth
from libs.exchange.bybit_models import ServerTime, WalletBalance, WalletCoinBalance
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
_WALLET_BALANCE_PATH = "/v5/account/wallet-balance"
_ALLOWED_PATHS = frozenset({"/v5/market/time", _WALLET_BALANCE_PATH})
_AUTH_ERROR_CODES = frozenset({10003, 10004})
_RATE_LIMIT_CODE = 10006
_GENERIC_BYBIT_ERROR_REASON = "Bybit read-only request returned non-zero retCode"


class BybitReadOnlyClient:
    """Stage 53-B1 read-only Bybit client skeleton.

    Scope: testnet/demo server time and wallet balance read-only queries only.
    No open positions, order status, orders, cancels, leverage, transfers,
    withdrawals, live reconcile, live execution, or service wiring.
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

    async def _signed_get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        endpoint_family: str,
    ) -> dict[str, Any]:
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

        _raise_for_bybit_error(payload, endpoint_family=endpoint_family)
        return payload

    async def get_server_time(self) -> ServerTime:
        payload = await self._signed_get(
            "/v5/market/time",
            endpoint_family="server_time",
        )
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

    async def get_wallet_balance(self) -> WalletBalance:
        payload = await self._signed_get(
            _WALLET_BALANCE_PATH,
            {"accountType": _to_bybit_account_type(self.settings.account_type)},
            endpoint_family="wallet_balance",
        )
        try:
            item = ((payload.get("result") or {}).get("list") or [])[0]
            coins = tuple(
                WalletCoinBalance(
                    coin=str(raw_coin["coin"]),
                    wallet_balance=_decimal_from_field(raw_coin, "walletBalance"),
                    equity=_decimal_from_field(raw_coin, "equity"),
                    available_to_withdraw=_optional_decimal_from_field(
                        raw_coin,
                        "availableToWithdraw",
                    ),
                )
                for raw_coin in item.get("coin") or []
            )
            if not coins:
                raise ValueError("wallet payload has no coin balances")
            return WalletBalance(
                exchange="bybit",
                account_type=str(item["accountType"]),
                total_equity=_decimal_from_field(item, "totalEquity"),
                total_wallet_balance=_decimal_from_field(item, "totalWalletBalance"),
                coins=coins,
            )
        except (DecimalException, IndexError, KeyError, TypeError, ValueError) as exc:
            raise ExchangeResponseError(
                ret_code=0,
                ret_msg="Bybit wallet balance payload missing required fields",
            ) from exc


def _raise_for_bybit_error(payload: dict[str, Any], *, endpoint_family: str) -> None:
    ret_code = int(payload.get("retCode", 0))
    if ret_code == 0:
        return
    if ret_code in _AUTH_ERROR_CODES:
        raise ExchangeAuthError(f"Bybit authentication failed (retCode {ret_code})")
    if ret_code == _RATE_LIMIT_CODE:
        raise ExchangeRateLimited(f"Bybit rate limited (retCode {ret_code})")
    raise ExchangeResponseError(
        ret_code=ret_code,
        ret_msg=f"{_GENERIC_BYBIT_ERROR_REASON}; endpoint_family={endpoint_family}",
    )


def _to_bybit_account_type(account_type: str) -> str:
    if account_type != "uta":
        raise ExchangeConfigurationError("Bybit B1 account_type must be uta")
    return "UNIFIED"


def _decimal_from_field(payload: dict[str, Any], field_name: str) -> Decimal:
    value = payload[field_name]
    if value in ("", None):
        raise ValueError(f"missing {field_name}")
    return Decimal(str(value))


def _optional_decimal_from_field(payload: dict[str, Any], field_name: str) -> Decimal | None:
    value = payload.get(field_name)
    if value in ("", None):
        return None
    return Decimal(str(value))
