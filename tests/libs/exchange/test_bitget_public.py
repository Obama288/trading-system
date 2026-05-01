from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from libs.exchange.bitget_public import BitgetPublicClient, BitgetServerTime
from libs.exchange.errors import ExchangeConfigurationError, ExchangeRateLimited, ExchangeResponseError, MarketDataUnavailable


_SERVER_TIME_PAYLOAD = {
    "code": "00000",
    "msg": "success",
    "requestTime": 1710000000123,
    "data": {
        "serverTime": "1710000000456",
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
    def __init__(self, payload: dict, captured: dict[str, object]) -> None:
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


def _patch_async(payload: dict, captured: dict[str, object]):
    mock_httpx = MagicMock()
    mock_httpx.AsyncClient.return_value = _FakeAsyncClient(payload, captured)
    return patch("libs.exchange.bitget_public.httpx", mock_httpx)


def test_client_repr_exposes_only_public_configuration():
    client = BitgetPublicClient()

    rendered = repr(client)

    assert "BitgetPublicClient" in rendered
    assert "base_url" in rendered
    assert "timeout" in rendered
    for forbidden in ("api_key", "api_secret", "passphrase", "paptrading"):
        assert forbidden not in rendered


@pytest.mark.asyncio
async def test_get_server_time_builds_expected_public_request_path_and_base_url():
    captured: dict[str, object] = {}

    with _patch_async(_SERVER_TIME_PAYLOAD, captured):
        server_time = await BitgetPublicClient().get_server_time()

    assert isinstance(server_time, BitgetServerTime)
    assert server_time.exchange == "bitget"
    assert server_time.server_time_ms == 1710000000456
    assert captured["url"] == "https://api.bitget.com/api/v2/public/time"


@pytest.mark.asyncio
async def test_get_server_time_uses_only_public_unsigned_headers():
    captured: dict[str, object] = {}

    with _patch_async(_SERVER_TIME_PAYLOAD, captured):
        await BitgetPublicClient().get_server_time()

    kwargs = captured["kwargs"]
    headers = kwargs["headers"]
    assert headers == {"User-Agent": "trading-system"}
    for forbidden in (
        "Authorization",
        "X-BAPI-API-KEY",
        "ACCESS-KEY",
        "ACCESS-SIGN",
        "ACCESS-PASSPHRASE",
        "paptrading",
    ):
        assert forbidden not in headers
    assert "params" not in kwargs


def test_private_or_authenticated_behavior_is_not_exposed():
    client = BitgetPublicClient()

    assert hasattr(client, "get_server_time")
    for forbidden in (
        "get_wallet_balance",
        "get_open_positions",
        "get_query_api_info",
        "place_order",
        "cancel_order",
        "set_leverage",
        "_signed_get",
    ):
        assert not hasattr(client, forbidden), f"Forbidden method exists: {forbidden}"


@pytest.mark.asyncio
async def test_only_allowed_public_endpoint_is_permitted():
    client = BitgetPublicClient()

    with pytest.raises(ExchangeConfigurationError):
        await client._public_get("/api/v2/mix/account/account")


@pytest.mark.asyncio
async def test_malformed_public_time_payload_raises_sanitized_error():
    captured: dict[str, object] = {}
    payload = {
        "code": "00000",
        "msg": "success",
        "data": {},
    }

    with _patch_async(payload, captured):
        with pytest.raises(ExchangeResponseError) as exc_info:
            await BitgetPublicClient().get_server_time()

    rendered = str(exc_info.value)
    assert "server time payload missing required fields" in rendered
    for forbidden in ("api_key", "api_secret", "passphrase", "paptrading"):
        assert forbidden not in rendered


@pytest.mark.asyncio
async def test_rate_limit_code_raises_rate_limited():
    captured: dict[str, object] = {}
    payload = {
        "code": "429",
        "msg": "too many requests",
        "requestTime": 1710000000123,
        "data": {},
    }

    with _patch_async(payload, captured):
        with pytest.raises(ExchangeRateLimited):
            await BitgetPublicClient().get_server_time()


@pytest.mark.asyncio
async def test_http_failure_raises_market_data_unavailable_without_network():
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

    with patch("libs.exchange.bitget_public.httpx", mock_httpx):
        with pytest.raises(MarketDataUnavailable):
            await BitgetPublicClient().get_server_time()
