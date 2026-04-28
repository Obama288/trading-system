from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr, ValidationError

from libs.config.settings import BybitB1Settings
from libs.exchange.bybit_models import ServerTime, WalletBalance
from libs.exchange.bybit_read_only import BybitReadOnlyClient
from libs.exchange.errors import (
    ExchangeAuthError,
    ExchangeConfigurationError,
    ExchangeRateLimited,
    ExchangeResponseError,
    MarketDataUnavailable,
)


FAKE_API_KEY = "testnet_fake_key"
FAKE_API_SECRET = "testnet_fake_secret"
FAKE_SIGNATURE = "deadbeefcafebabefeedface1234567890abcdef"


_WALLET_BALANCE_PAYLOAD = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "list": [
            {
                "accountType": "UNIFIED",
                "accountIMRate": "0.01",
                "accountMMRate": "0.005",
                "totalEquity": "12345.67",
                "totalWalletBalance": "12000.00",
                "accountId": "123456789",
                "coin": [
                    {
                        "coin": "USDT",
                        "walletBalance": "12000.00",
                        "equity": "12345.67",
                        "availableToWithdraw": "1000.00",
                    }
                ],
            }
        ]
    },
}


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class _FakeAsyncClient:
    def __init__(self, payload: dict, captured: dict) -> None:
        self._payload = payload
        self._captured = captured

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def get(self, url: str, **kwargs: object) -> _FakeResponse:
        self._captured["url"] = url
        self._captured["kwargs"] = kwargs
        return _FakeResponse(self._payload)


def _settings(environment: str = "testnet") -> BybitB1Settings:
    return BybitB1Settings(
        environment=environment,
        api_key=SecretStr(FAKE_API_KEY),
        api_secret=SecretStr(FAKE_API_SECRET),
    )


def _patch_async(payload: dict, captured: dict):
    mock_httpx = MagicMock()
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(payload, captured)
    return patch("libs.exchange.bybit_read_only.httpx", mock_httpx)


def test_client_repr_does_not_leak_credentials():
    client = BybitReadOnlyClient(_settings())

    rendered = repr(client)

    assert FAKE_API_KEY not in rendered
    assert FAKE_API_SECRET not in rendered


def test_missing_credentials_fail_closed():
    with pytest.raises(ExchangeAuthError):
        BybitReadOnlyClient(BybitB1Settings(api_key=None, api_secret=None))


@pytest.mark.parametrize("environment", ["production", "live"])
def test_production_and_live_environment_rejected_by_settings(environment: str):
    with pytest.raises(ValidationError):
        BybitB1Settings(
            environment=environment,
            api_key=SecretStr(FAKE_API_KEY),
            api_secret=SecretStr(FAKE_API_SECRET),
        )


@pytest.mark.parametrize("base_url", ["https://api.bybit.com", "https://api.bytick.com"])
def test_production_private_base_url_rejected(base_url: str):
    with pytest.raises(ExchangeConfigurationError):
        BybitReadOnlyClient(_settings(), base_url=base_url)


def test_unsupported_endpoint_method_fails_closed():
    client = BybitReadOnlyClient(_settings())

    with pytest.raises(ExchangeConfigurationError):
        # Protected internal helper: any future endpoint must be explicitly allowed.
        import asyncio

        asyncio.run(
            client._signed_get(
                "/v5/order/realtime",
                endpoint_family="order_status",
            )
        )


@pytest.mark.asyncio
async def test_get_server_time_uses_mocked_http_and_returns_model():
    payload = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "timeSecond": "1700000000",
            "timeNano": "1700000000123456789",
        },
    }
    captured: dict = {}

    with _patch_async(payload, captured):
        server_time = await BybitReadOnlyClient(_settings()).get_server_time()

    assert isinstance(server_time, ServerTime)
    assert server_time.exchange == "bybit"
    assert server_time.time_second == 1700000000
    assert server_time.time_nano == 1700000000123456789
    assert captured["url"] == "https://api-testnet.bybit.com/v5/market/time"


@pytest.mark.asyncio
async def test_get_server_time_sends_auth_headers_without_logging_them(caplog):
    payload = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "timeSecond": "1700000000",
            "timeNano": "1700000000123456789",
        },
    }
    captured: dict = {}

    with _patch_async(payload, captured):
        await BybitReadOnlyClient(_settings()).get_server_time()

    headers = captured["kwargs"]["headers"]
    assert headers["X-BAPI-API-KEY"] == FAKE_API_KEY
    assert "X-BAPI-SIGN" in headers
    assert FAKE_API_KEY not in caplog.text
    assert FAKE_API_SECRET not in caplog.text
    assert headers["X-BAPI-SIGN"] not in caplog.text


@pytest.mark.asyncio
async def test_auth_error_code_raises_sanitized_auth_error():
    captured: dict = {}
    with _patch_async({"retCode": 10004, "retMsg": "bad sign"}, captured):
        with pytest.raises(ExchangeAuthError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_server_time()

    rendered = str(exc_info.value)
    assert "10004" in rendered
    assert FAKE_API_KEY not in rendered
    assert FAKE_API_SECRET not in rendered
    assert "bad sign" not in rendered


@pytest.mark.asyncio
async def test_rate_limit_code_raises_rate_limited():
    captured: dict = {}
    with _patch_async({"retCode": 10006, "retMsg": "too many requests"}, captured):
        with pytest.raises(ExchangeRateLimited):
            await BybitReadOnlyClient(_settings()).get_server_time()


@pytest.mark.asyncio
async def test_generic_bybit_error_raises_response_error():
    captured: dict = {}
    with _patch_async({"retCode": 10001, "retMsg": "bad request"}, captured):
        with pytest.raises(ExchangeResponseError):
            await BybitReadOnlyClient(_settings()).get_server_time()


@pytest.mark.asyncio
async def test_generic_bybit_error_sanitizes_sensitive_ret_msg(caplog):
    fake_account_id = "account_id=123456789"
    fake_balance = "balance=999999.99"
    sensitive_ret_msg = (
        f"bad request api_key={FAKE_API_KEY} api_secret={FAKE_API_SECRET} "
        f"X-BAPI-SIGN={FAKE_SIGNATURE} X-BAPI-API-KEY={FAKE_API_KEY} "
        f"signed_payload=timestamp-key-window-query {fake_account_id} {fake_balance} "
        "raw_private_payload={'walletBalance':'999999.99'}"
    )
    captured: dict = {}

    with _patch_async({"retCode": 10001, "retMsg": sensitive_ret_msg}, captured):
        with pytest.raises(ExchangeResponseError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_server_time()

    exposed_text = " ".join(
        [
            str(exc_info.value),
            repr(exc_info.value),
            caplog.text,
        ]
    )
    assert "10001" in exposed_text
    assert "endpoint_family=server_time" in exposed_text
    for forbidden in (
        FAKE_API_KEY,
        FAKE_API_SECRET,
        FAKE_SIGNATURE,
        "X-BAPI-SIGN",
        "X-BAPI-API-KEY",
        "signed_payload",
        fake_account_id,
        fake_balance,
        "walletBalance",
        "raw_private_payload",
        sensitive_ret_msg,
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
async def test_get_wallet_balance_uses_mocked_http_and_returns_decimal_model():
    captured: dict = {}

    with _patch_async(_WALLET_BALANCE_PAYLOAD, captured):
        wallet = await BybitReadOnlyClient(_settings()).get_wallet_balance()

    assert isinstance(wallet, WalletBalance)
    assert wallet.exchange == "bybit"
    assert wallet.account_type == "UNIFIED"
    assert wallet.total_equity == Decimal("12345.67")
    assert wallet.total_wallet_balance == Decimal("12000.00")
    assert wallet.coins[0].coin == "USDT"
    assert wallet.coins[0].wallet_balance == Decimal("12000.00")
    assert wallet.coins[0].equity == Decimal("12345.67")
    assert wallet.coins[0].available_to_withdraw == Decimal("1000.00")
    assert captured["url"] == "https://api-testnet.bybit.com/v5/account/wallet-balance"
    assert captured["kwargs"]["params"] == {"accountType": "UNIFIED"}


@pytest.mark.asyncio
async def test_get_wallet_balance_sends_auth_headers_without_logging_them(caplog):
    captured: dict = {}

    with _patch_async(_WALLET_BALANCE_PAYLOAD, captured):
        await BybitReadOnlyClient(_settings()).get_wallet_balance()

    headers = captured["kwargs"]["headers"]
    assert headers["X-BAPI-API-KEY"] == FAKE_API_KEY
    assert "X-BAPI-SIGN" in headers
    assert FAKE_API_KEY not in caplog.text
    assert FAKE_API_SECRET not in caplog.text
    assert headers["X-BAPI-SIGN"] not in caplog.text


@pytest.mark.asyncio
async def test_wallet_balance_repr_and_model_dump_redact_balances_and_account_ids():
    captured: dict = {}

    with _patch_async(_WALLET_BALANCE_PAYLOAD, captured):
        wallet = await BybitReadOnlyClient(_settings()).get_wallet_balance()

    exposed_text = " ".join(
        [
            repr(wallet),
            repr(wallet.coins[0]),
            str(wallet.model_dump()),
            str(wallet.coins[0].model_dump()),
        ]
    )
    for forbidden in (
        "12345.67",
        "12000.00",
        "1000.00",
        "123456789",
        "walletBalance",
        "totalWalletBalance",
        "totalEquity",
        "accountId",
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
async def test_wallet_generic_error_sanitizes_sensitive_ret_msg(caplog):
    sensitive_ret_msg = (
        f"wallet error api_key={FAKE_API_KEY} api_secret={FAKE_API_SECRET} "
        f"X-BAPI-SIGN={FAKE_SIGNATURE} X-BAPI-API-KEY={FAKE_API_KEY} "
        "signed_payload=timestamp-key-window-accountType "
        "account_id=123456789 balance=999999.99 "
        "raw_wallet_payload={'totalWalletBalance':'999999.99'}"
    )
    captured: dict = {}

    with _patch_async({"retCode": 10001, "retMsg": sensitive_ret_msg}, captured):
        with pytest.raises(ExchangeResponseError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_wallet_balance()

    exposed_text = " ".join([str(exc_info.value), repr(exc_info.value), caplog.text])
    assert "10001" in exposed_text
    assert "endpoint_family=wallet_balance" in exposed_text
    for forbidden in (
        FAKE_API_KEY,
        FAKE_API_SECRET,
        FAKE_SIGNATURE,
        "X-BAPI-SIGN",
        "X-BAPI-API-KEY",
        "signed_payload",
        "account_id=123456789",
        "balance=999999.99",
        "totalWalletBalance",
        "raw_wallet_payload",
        sensitive_ret_msg,
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
async def test_malformed_wallet_payload_raises_sanitized_response_error(caplog):
    malformed = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "list": [
                {
                    "accountType": "UNIFIED",
                    "accountId": "123456789",
                    "totalEquity": "12345.67",
                    "totalWalletBalance": "12000.00",
                    "coin": [{"coin": "USDT", "walletBalance": "not-a-decimal"}],
                }
            ]
        },
    }
    captured: dict = {}

    with _patch_async(malformed, captured):
        with pytest.raises(ExchangeResponseError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_wallet_balance()

    exposed_text = " ".join([str(exc_info.value), repr(exc_info.value), caplog.text])
    assert "wallet balance payload missing required fields" in exposed_text
    for forbidden in (
        "12345.67",
        "12000.00",
        "123456789",
        "not-a-decimal",
        "walletBalance",
        "accountId",
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
async def test_malformed_server_time_payload_raises_response_error():
    captured: dict = {}
    with _patch_async({"retCode": 0, "retMsg": "OK", "result": {}}, captured):
        with pytest.raises(ExchangeResponseError):
            await BybitReadOnlyClient(_settings()).get_server_time()


@pytest.mark.asyncio
async def test_http_failure_raises_unavailable_without_secret_leak():
    class _FailingClient:
        async def __aenter__(self) -> "_FailingClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

        async def get(self, url: str, **kwargs: object) -> _FakeResponse:
            import httpx

            raise httpx.ConnectTimeout("timeout")

    mock_httpx = MagicMock()
    mock_httpx.AsyncClient.return_value = _FailingClient()

    with patch("libs.exchange.bybit_read_only.httpx", mock_httpx):
        with pytest.raises(MarketDataUnavailable) as exc_info:
            await BybitReadOnlyClient(_settings()).get_server_time()

    rendered = str(exc_info.value)
    assert FAKE_API_KEY not in rendered
    assert FAKE_API_SECRET not in rendered


def test_only_server_time_and_wallet_balance_exist_among_client_query_methods():
    client = BybitReadOnlyClient(_settings())

    assert hasattr(client, "get_server_time")
    assert hasattr(client, "get_wallet_balance")
    for forbidden in (
        "get_open_positions",
        "get_order_status",
        "place_order",
        "cancel_order",
        "set_leverage",
        "withdraw",
        "transfer",
        "live_reconcile",
        "live_execution",
    ):
        assert not hasattr(client, forbidden), f"Forbidden method exists: {forbidden}"
