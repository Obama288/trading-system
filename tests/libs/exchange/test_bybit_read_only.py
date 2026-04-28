from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr, ValidationError

from libs.config.settings import BybitB1Settings
from libs.exchange.bybit_models import ServerTime
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

        asyncio.run(client._signed_get("/v5/account/wallet-balance"))


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
    fake_signature = "deadbeefcafebabefeedface1234567890abcdef"
    fake_account_id = "account_id=123456789"
    fake_balance = "balance=999999.99"
    sensitive_ret_msg = (
        f"bad request api_key={FAKE_API_KEY} api_secret={FAKE_API_SECRET} "
        f"X-BAPI-SIGN={fake_signature} X-BAPI-API-KEY={FAKE_API_KEY} "
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
        fake_signature,
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


def test_only_get_server_time_exists_among_client_query_methods():
    client = BybitReadOnlyClient(_settings())

    assert hasattr(client, "get_server_time")
    for forbidden in (
        "get_wallet_balance",
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
