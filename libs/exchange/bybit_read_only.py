from __future__ import annotations

from decimal import Decimal, DecimalException
from typing import Any

import httpx
from httpx import HTTPError

from libs.config.settings import BybitB1Settings
from libs.exchange.bybit_auth import BybitAuth, canonical_query, now_ms
from libs.exchange.bybit_models import (
    ApiKeyInfo,
    OpenPosition,
    OpenPositions,
    ServerTime,
    WalletBalance,
    WalletCoinBalance,
)
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
_SERVER_TIME_PATH = "/v5/market/time"
_QUERY_API_PATH = "/v5/user/query-api"
_WALLET_BALANCE_PATH = "/v5/account/wallet-balance"
_OPEN_POSITIONS_PATH = "/v5/position/list"
_SIGNED_ALLOWED_PATHS = frozenset({_QUERY_API_PATH, _WALLET_BALANCE_PATH, _OPEN_POSITIONS_PATH})
_AUTH_ERROR_CODES = frozenset({10002, 10003, 10004, 10005, 10007, 10010})
_RATE_LIMIT_CODE = 10006
_RETCODE_ERROR_CATEGORIES = {
    10002: "timestamp_or_recv_window_error",
    10003: "invalid_key_or_environment",
    10004: "invalid_signature",
    10005: "permission_denied",
    10006: "rate_limited",
    10007: "authentication_failed",
    10010: "ip_mismatch",
}
_GENERIC_BYBIT_ERROR_REASON = "Bybit read-only request returned non-zero retCode"
_UNSAFE_PERMISSION_TOKENS = frozenset({
    "withdraw",
    "transfer",
    "order",
    "trade",
    "write",
})


class BybitReadOnlyClient:
    """Stage 53-B1 read-only Bybit client skeleton.

    Scope: testnet/demo server time, wallet balance, and open positions
    read-only queries only. Open positions are external observations, not
    internal trading authority. No order status, orders, cancels, leverage,
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

        resolved_base_url = (base_url or _TESTNET_BASE_URL).rstrip("/")
        if resolved_base_url in _PRODUCTION_BASE_URLS:
            raise ExchangeConfigurationError("production Bybit base URL is forbidden")
        if "api.bybit.com" in resolved_base_url or "api.bytick.com" in resolved_base_url:
            raise ExchangeConfigurationError("production Bybit base URL is forbidden")

        self.settings = settings
        self.base_url = resolved_base_url
        self.timeout = timeout
        self._recv_window_ms = recv_window_ms

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
        if path not in _SIGNED_ALLOWED_PATHS:
            raise ExchangeConfigurationError(f"Bybit endpoint not allowed in B1 slice: {path}")
        if self.settings.api_key is None or self.settings.api_secret is None:
            raise ExchangeAuthError("Bybit B1 credentials are required for private read-only request")

        url = f"{self.base_url}{path}"
        auth = BybitAuth(
            api_key=self.settings.api_key,
            api_secret=self.settings.api_secret,
            recv_window_ms=self._recv_window_ms,
        )
        headers = auth.signed_headers(query_params=params)
        query_string = canonical_query(params)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=query_string, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except HTTPError as exc:
            raise MarketDataUnavailable(f"Bybit read-only request failed [{path}]") from exc

        _raise_for_bybit_error(payload, endpoint_family=endpoint_family)
        return payload

    async def _public_get(
        self,
        path: str,
        *,
        endpoint_family: str,
    ) -> dict[str, Any]:
        if path != _SERVER_TIME_PATH:
            raise ExchangeConfigurationError(f"Bybit public endpoint not allowed in B1 slice: {path}")

        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
        except HTTPError as exc:
            raise MarketDataUnavailable(f"Bybit read-only request failed [{path}]") from exc

        _raise_for_bybit_error(payload, endpoint_family=endpoint_family)
        return payload

    async def get_server_time(self) -> ServerTime:
        payload = await self._public_get(
            _SERVER_TIME_PATH,
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

    async def get_query_api_info(self) -> ApiKeyInfo:
        payload = await self._signed_get(
            _QUERY_API_PATH,
            endpoint_family="query_api",
        )
        result = payload.get("result") or {}
        try:
            read_only = _parse_read_only(result.get("readOnly"))
            permissions_safe = _permissions_are_safe(result.get("permissions"))
            key_active, deadline_present, expired_at_present = _parse_key_active(result)
        except (TypeError, ValueError) as exc:
            raise _with_bybit_error_metadata(
                ExchangeAuthError("Bybit query-api preflight failed"),
                category="preflight_failed",
                ret_code=0,
            ) from exc

        if not read_only or not permissions_safe or not key_active:
            raise _with_bybit_error_metadata(
                ExchangeAuthError("Bybit query-api preflight failed"),
                category="preflight_failed",
                ret_code=0,
            )

        return ApiKeyInfo(
            exchange="bybit",
            read_only=read_only,
            permissions_safe=permissions_safe,
            key_active=key_active,
            deadline_days_present=deadline_present,
            expired_at_present=expired_at_present,
        )

    async def get_open_positions(self) -> OpenPositions:
        payload = await self._signed_get(
            _OPEN_POSITIONS_PATH,
            {"category": "linear", "settleCoin": "USDT"},
            endpoint_family="open_positions",
        )
        try:
            result = payload.get("result") or {}
            raw_positions = result["list"]
            positions = tuple(
                OpenPosition(
                    symbol=str(raw_position["symbol"]),
                    side=str(raw_position["side"]),
                    size=_decimal_from_field(raw_position, "size"),
                    avg_price=_decimal_from_field(raw_position, "avgPrice"),
                    mark_price=_decimal_from_field(raw_position, "markPrice"),
                    position_value=_decimal_from_field(raw_position, "positionValue"),
                    unrealised_pnl=_decimal_from_field(raw_position, "unrealisedPnl"),
                    position_im=_decimal_from_field(raw_position, "positionIM"),
                    position_mm=_decimal_from_field(raw_position, "positionMM"),
                    leverage=_decimal_from_field(raw_position, "leverage"),
                )
                for raw_position in raw_positions
                if _decimal_from_field(raw_position, "size") != Decimal("0")
            )
            return OpenPositions(
                exchange="bybit",
                category=str(result["category"]),
                positions=positions,
            )
        except (DecimalException, KeyError, TypeError, ValueError) as exc:
            raise ExchangeResponseError(
                ret_code=0,
                ret_msg="Bybit open positions payload missing required fields",
            ) from exc


def _raise_for_bybit_error(payload: dict[str, Any], *, endpoint_family: str) -> None:
    ret_code = int(payload.get("retCode", 0))
    if ret_code == 0:
        return
    category = _RETCODE_ERROR_CATEGORIES.get(ret_code, "response_error")
    if ret_code in _AUTH_ERROR_CODES:
        raise _with_bybit_error_metadata(
            ExchangeAuthError(f"Bybit authentication failed (retCode {ret_code})"),
            category=category,
            ret_code=ret_code,
        )
    if ret_code == _RATE_LIMIT_CODE:
        raise _with_bybit_error_metadata(
            ExchangeRateLimited(f"Bybit rate limited (retCode {ret_code})"),
            category=category,
            ret_code=ret_code,
        )
    raise _with_bybit_error_metadata(
        ExchangeResponseError(
            ret_code=ret_code,
            ret_msg=f"{_GENERIC_BYBIT_ERROR_REASON}; endpoint_family={endpoint_family}",
        ),
        category=category,
        ret_code=ret_code,
    )


def _with_bybit_error_metadata(
    exc: Exception,
    *,
    category: str,
    ret_code: int,
) -> Exception:
    setattr(exc, "error_category", category)
    setattr(exc, "ret_code", ret_code)
    return exc


def _parse_read_only(value: Any) -> bool:
    if value in (1, "1", True):
        return True
    if value in (0, "0", False):
        return False
    raise ValueError("missing readOnly")


def _permissions_are_safe(value: Any) -> bool:
    if value in ({}, [], (), None):
        return True
    for token in _permission_tokens(value):
        lower = token.lower()
        if any(unsafe in lower for unsafe in _UNSAFE_PERMISSION_TOKENS):
            return False
    return True


def _permission_tokens(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        tokens: list[str] = []
        for key, nested in value.items():
            tokens.append(str(key))
            tokens.extend(_permission_tokens(nested))
        return tuple(tokens)
    if isinstance(value, (list, tuple, set)):
        tokens = []
        for nested in value:
            tokens.extend(_permission_tokens(nested))
        return tuple(tokens)
    if isinstance(value, str):
        return (value,)
    if value is None:
        return ()
    return (str(value),)


def _parse_key_active(result: dict[str, Any]) -> tuple[bool, bool, bool]:
    deadline_present = "deadlineDay" in result and result.get("deadlineDay") not in ("", None)
    expired_at_present = "expiredAt" in result and result.get("expiredAt") not in ("", None)

    if deadline_present:
        try:
            deadline_days = int(str(result["deadlineDay"]))
        except (TypeError, ValueError) as exc:
            raise ValueError("malformed deadlineDay") from exc
        return deadline_days > 0, True, expired_at_present

    if expired_at_present:
        try:
            expired_at_ms = int(str(result["expiredAt"]))
        except (TypeError, ValueError) as exc:
            raise ValueError("malformed expiredAt") from exc
        return expired_at_ms > now_ms(), False, True

    raise ValueError("query-api payload missing expiry metadata")


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
