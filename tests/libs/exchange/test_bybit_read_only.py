from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr, ValidationError

from libs.config.settings import BybitB1Settings
from libs.exchange.bybit_auth import BybitAuth, canonical_query
from libs.exchange.bybit_models import ApiKeyInfo, OpenPositions, ServerTime, WalletBalance
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

_OPEN_POSITIONS_PAYLOAD = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "category": "linear",
        "nextPageCursor": "",
        "list": [
            {
                "positionIdx": 0,
                "riskId": 1,
                "riskLimitValue": "2000000",
                "symbol": "BTCUSDT",
                "side": "Buy",
                "size": "0.25",
                "avgPrice": "64000.50",
                "markPrice": "64123.45",
                "positionValue": "16000.125",
                "unrealisedPnl": "30.7375",
                "positionIM": "800.00625",
                "positionMM": "80.000625",
                "leverage": "20",
                "accountId": "123456789",
            },
            {
                "symbol": "ETHUSDT",
                "side": "Sell",
                "size": "0",
                "avgPrice": "3000",
                "markPrice": "3001",
                "positionValue": "0",
                "unrealisedPnl": "0",
                "positionIM": "0",
                "positionMM": "0",
                "leverage": "10",
            },
        ],
    },
}

_QUERY_API_PAYLOAD = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "id": "sensitive-user-id",
        "note": "do-not-print",
        "readOnly": 1,
        "deadlineDay": 7,
        "expiredAt": "4102444800000",
        "ips": ["192.0.2.1"],
        "permissions": {
            "Account": ["read"],
            "Spot": ["read"],
        },
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


@pytest.mark.asyncio
async def test_server_time_allows_missing_credentials_but_private_reads_fail_closed():
    payload = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "timeSecond": "1700000000",
            "timeNano": "1700000000123456789",
        },
    }
    captured: dict = {}
    client = BybitReadOnlyClient(BybitB1Settings(api_key=None, api_secret=None))

    with _patch_async(payload, captured):
        server_time = await client.get_server_time()

    assert server_time.time_second == 1700000000
    assert "headers" not in captured["kwargs"]
    with pytest.raises(ExchangeAuthError):
        await client.get_wallet_balance()


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
async def test_get_server_time_uses_unsigned_public_request_without_logging_auth(caplog):
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

    assert "headers" not in captured["kwargs"]
    assert "params" not in captured["kwargs"]
    assert FAKE_API_KEY not in caplog.text
    assert FAKE_API_SECRET not in caplog.text


@pytest.mark.asyncio
async def test_auth_error_code_raises_sanitized_auth_error():
    captured: dict = {}
    with _patch_async({"retCode": 10004, "retMsg": "bad sign"}, captured):
        with pytest.raises(ExchangeAuthError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_server_time()

    rendered = str(exc_info.value)
    assert "10004" in rendered
    assert getattr(exc_info.value, "error_category") == "invalid_signature"
    assert getattr(exc_info.value, "ret_code") == 10004
    assert FAKE_API_KEY not in rendered
    assert FAKE_API_SECRET not in rendered
    assert "bad sign" not in rendered


@pytest.mark.asyncio
async def test_rate_limit_code_raises_rate_limited_with_safe_category():
    captured: dict = {}
    with _patch_async({"retCode": 10006, "retMsg": "too many requests"}, captured):
        with pytest.raises(ExchangeRateLimited) as exc_info:
            await BybitReadOnlyClient(_settings()).get_server_time()

    assert getattr(exc_info.value, "error_category") == "rate_limited"
    assert getattr(exc_info.value, "ret_code") == 10006

@pytest.mark.asyncio
async def test_generic_bybit_error_raises_response_error():
    captured: dict = {}
    with _patch_async({"retCode": 10001, "retMsg": "bad request"}, captured):
        with pytest.raises(ExchangeResponseError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_server_time()

    assert getattr(exc_info.value, "error_category") == "response_error"
    assert getattr(exc_info.value, "ret_code") == 10001


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("ret_code", "category"),
    [
        (10002, "timestamp_or_recv_window_error"),
        (10003, "invalid_key_or_environment"),
        (10004, "invalid_signature"),
        (10005, "permission_denied"),
        (10007, "authentication_failed"),
        (10010, "ip_mismatch"),
    ],
)
async def test_auth_ret_codes_have_safe_granular_categories(ret_code: int, category: str):
    sensitive_ret_msg = (
        f"auth failure api_key={FAKE_API_KEY} api_secret={FAKE_API_SECRET} "
        f"X-BAPI-SIGN={FAKE_SIGNATURE} raw_private_payload=secret"
    )
    captured: dict = {}

    with _patch_async({"retCode": ret_code, "retMsg": sensitive_ret_msg}, captured):
        with pytest.raises(ExchangeAuthError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_wallet_balance()

    exposed_text = str(exc_info.value)
    assert getattr(exc_info.value, "error_category") == category
    assert getattr(exc_info.value, "ret_code") == ret_code
    assert str(ret_code) in exposed_text
    for forbidden in (
        FAKE_API_KEY,
        FAKE_API_SECRET,
        FAKE_SIGNATURE,
        "raw_private_payload",
        sensitive_ret_msg,
    ):
        assert forbidden not in exposed_text


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
    assert captured["kwargs"]["params"] == "accountType=UNIFIED"


@pytest.mark.asyncio
async def test_get_wallet_balance_sends_auth_headers_without_logging_them(caplog):
    captured: dict = {}

    with _patch_async(_WALLET_BALANCE_PAYLOAD, captured):
        await BybitReadOnlyClient(_settings()).get_wallet_balance()

    headers = captured["kwargs"]["headers"]
    assert headers["X-BAPI-API-KEY"] == FAKE_API_KEY
    assert headers["X-BAPI-SIGN-TYPE"] == "2"
    assert "X-BAPI-SIGN" in headers
    assert FAKE_API_KEY not in caplog.text
    assert FAKE_API_SECRET not in caplog.text
    assert headers["X-BAPI-SIGN"] not in caplog.text


@pytest.mark.asyncio
async def test_wallet_balance_signed_query_matches_sent_query(monkeypatch):
    captured: dict = {}
    signed: dict = {}
    original_signed_headers = BybitAuth.signed_headers

    def _capturing_signed_headers(self: BybitAuth, **kwargs: object) -> dict[str, str]:
        signed["query_params"] = kwargs.get("query_params")
        signed["query_string"] = canonical_query(kwargs.get("query_params"))  # type: ignore[arg-type]
        return original_signed_headers(self, **kwargs)

    monkeypatch.setattr(BybitAuth, "signed_headers", _capturing_signed_headers)

    with _patch_async(_WALLET_BALANCE_PAYLOAD, captured):
        await BybitReadOnlyClient(_settings()).get_wallet_balance()

    assert signed["query_params"] == {"accountType": "UNIFIED"}
    assert signed["query_string"] == "accountType=UNIFIED"
    assert captured["kwargs"]["params"] == signed["query_string"]


@pytest.mark.asyncio
async def test_signed_query_uses_deterministic_canonical_order_for_multi_param_get():
    captured: dict = {}

    with _patch_async(_OPEN_POSITIONS_PAYLOAD, captured):
        await BybitReadOnlyClient(_settings()).get_open_positions()

    assert captured["kwargs"]["params"] == "category=linear&settleCoin=USDT"


@pytest.mark.asyncio
async def test_get_query_api_info_uses_signed_read_only_endpoint_and_returns_safe_model():
    captured: dict = {}

    with _patch_async(_QUERY_API_PAYLOAD, captured):
        info = await BybitReadOnlyClient(_settings()).get_query_api_info()

    assert isinstance(info, ApiKeyInfo)
    assert info.exchange == "bybit"
    assert info.read_only is True
    assert info.permissions_safe is True
    assert info.key_active is True
    assert info.deadline_days_present is True
    assert info.expired_at_present is True
    assert captured["url"] == "https://api-testnet.bybit.com/v5/user/query-api"
    assert captured["kwargs"]["params"] == ""
    headers = captured["kwargs"]["headers"]
    assert headers["X-BAPI-SIGN-TYPE"] == "2"


@pytest.mark.asyncio
async def test_query_api_info_repr_and_model_dump_do_not_expose_raw_metadata():
    captured: dict = {}

    with _patch_async(_QUERY_API_PAYLOAD, captured):
        info = await BybitReadOnlyClient(_settings()).get_query_api_info()

    exposed_text = " ".join([repr(info), str(info.model_dump())])
    for forbidden in (
        "sensitive-user-id",
        "do-not-print",
        "Account",
        "Spot",
        "192.0.2.1",
        "4102444800000",
        "deadlineDay",
        "expiredAt",
        "ips",
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "result_update",
    [
        {"readOnly": 0},
        {"readOnly": None},
        {"permissions": {"Withdraw": ["read"]}},
        {"permissions": {"ContractTrade": ["Order"]}},
        {"permissions": {"Transfer": ["read"]}},
        {"deadlineDay": 0},
        {"deadlineDay": -1},
        {"deadlineDay": None, "expiredAt": None},
        {"deadlineDay": None},
    ],
)
async def test_query_api_preflight_failures_are_sanitized(result_update: dict):
    captured: dict = {}
    payload = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            **_QUERY_API_PAYLOAD["result"],
            **result_update,
        },
    }
    if result_update == {"deadlineDay": None}:
        payload["result"].pop("expiredAt", None)

    with _patch_async(payload, captured):
        with pytest.raises(ExchangeAuthError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_query_api_info()

    exposed_text = str(exc_info.value)
    assert getattr(exc_info.value, "error_category") == "preflight_failed"
    assert getattr(exc_info.value, "ret_code") == 0
    for forbidden in (
        "sensitive-user-id",
        "ContractTrade",
        "Withdraw",
        "Transfer",
        "Order",
        "192.0.2.1",
        "4102444800000",
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expired_at",
    [
        "1",
        "not-a-timestamp",
    ],
)
async def test_query_api_expired_at_stale_or_malformed_fails_closed(expired_at: str):
    captured: dict = {}
    payload = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            **_QUERY_API_PAYLOAD["result"],
            "deadlineDay": None,
            "expiredAt": expired_at,
        },
    }

    with _patch_async(payload, captured):
        with pytest.raises(ExchangeAuthError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_query_api_info()

    exposed_text = str(exc_info.value)
    assert getattr(exc_info.value, "error_category") == "preflight_failed"
    assert getattr(exc_info.value, "ret_code") == 0
    assert expired_at not in exposed_text
    assert "expiredAt" not in exposed_text
    assert "sensitive-user-id" not in exposed_text


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


@pytest.mark.asyncio
async def test_get_open_positions_uses_mocked_http_and_returns_decimal_external_observations():
    captured: dict = {}

    with _patch_async(_OPEN_POSITIONS_PAYLOAD, captured):
        positions = await BybitReadOnlyClient(_settings()).get_open_positions()

    assert isinstance(positions, OpenPositions)
    assert positions.exchange == "bybit"
    assert positions.category == "linear"
    assert len(positions.positions) == 1
    position = positions.positions[0]
    assert position.symbol == "BTCUSDT"
    assert position.side == "Buy"
    assert position.size == Decimal("0.25")
    assert position.avg_price == Decimal("64000.50")
    assert position.mark_price == Decimal("64123.45")
    assert position.position_value == Decimal("16000.125")
    assert position.unrealised_pnl == Decimal("30.7375")
    assert position.position_im == Decimal("800.00625")
    assert position.position_mm == Decimal("80.000625")
    assert position.leverage == Decimal("20")
    assert captured["url"] == "https://api-testnet.bybit.com/v5/position/list"
    assert captured["kwargs"]["params"] == "category=linear&settleCoin=USDT"


@pytest.mark.asyncio
async def test_get_open_positions_sends_auth_headers_without_logging_them(caplog):
    captured: dict = {}

    with _patch_async(_OPEN_POSITIONS_PAYLOAD, captured):
        await BybitReadOnlyClient(_settings()).get_open_positions()

    headers = captured["kwargs"]["headers"]
    assert headers["X-BAPI-API-KEY"] == FAKE_API_KEY
    assert headers["X-BAPI-SIGN-TYPE"] == "2"
    assert "X-BAPI-SIGN" in headers
    assert FAKE_API_KEY not in caplog.text
    assert FAKE_API_SECRET not in caplog.text
    assert headers["X-BAPI-SIGN"] not in caplog.text


@pytest.mark.asyncio
async def test_open_positions_repr_and_model_dump_redact_private_observation_values():
    captured: dict = {}

    with _patch_async(_OPEN_POSITIONS_PAYLOAD, captured):
        positions = await BybitReadOnlyClient(_settings()).get_open_positions()

    exposed_text = " ".join(
        [
            repr(positions),
            repr(positions.positions[0]),
            str(positions.model_dump()),
            str(positions.positions[0].model_dump()),
        ]
    )
    for forbidden in (
        "BTCUSDT",
        "ETHUSDT",
        "0.25",
        "64000.50",
        "64123.45",
        "16000.125",
        "30.7375",
        "800.00625",
        "80.000625",
        "123456789",
        "accountId",
        "positionValue",
        "unrealisedPnl",
        "positionIM",
        "positionMM",
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
async def test_open_positions_generic_error_sanitizes_sensitive_ret_msg(caplog):
    sensitive_ret_msg = (
        f"position error api_key={FAKE_API_KEY} api_secret={FAKE_API_SECRET} "
        f"X-BAPI-SIGN={FAKE_SIGNATURE} X-BAPI-API-KEY={FAKE_API_KEY} "
        "signed_payload=timestamp-key-window-category "
        "account_id=123456789 symbol=BTCUSDT size=0.25 pnl=30.7375 margin=800.00625 "
        "raw_position_payload={'symbol':'BTCUSDT','size':'0.25'}"
    )
    captured: dict = {}

    with _patch_async({"retCode": 10001, "retMsg": sensitive_ret_msg}, captured):
        with pytest.raises(ExchangeResponseError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_open_positions()

    exposed_text = " ".join([str(exc_info.value), repr(exc_info.value), caplog.text])
    assert "10001" in exposed_text
    assert "endpoint_family=open_positions" in exposed_text
    for forbidden in (
        FAKE_API_KEY,
        FAKE_API_SECRET,
        FAKE_SIGNATURE,
        "X-BAPI-SIGN",
        "X-BAPI-API-KEY",
        "signed_payload",
        "account_id=123456789",
        "BTCUSDT",
        "0.25",
        "30.7375",
        "800.00625",
        "raw_position_payload",
        sensitive_ret_msg,
    ):
        assert forbidden not in exposed_text


@pytest.mark.asyncio
async def test_malformed_open_positions_payload_raises_sanitized_response_error(caplog):
    malformed = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "category": "linear",
            "list": [
                {
                    "symbol": "BTCUSDT",
                    "side": "Buy",
                    "size": "not-a-decimal",
                    "avgPrice": "64000.50",
                    "markPrice": "64123.45",
                    "positionValue": "16000.125",
                    "unrealisedPnl": "30.7375",
                    "positionIM": "800.00625",
                    "positionMM": "80.000625",
                    "leverage": "20",
                    "accountId": "123456789",
                }
            ],
        },
    }
    captured: dict = {}

    with _patch_async(malformed, captured):
        with pytest.raises(ExchangeResponseError) as exc_info:
            await BybitReadOnlyClient(_settings()).get_open_positions()

    exposed_text = " ".join([str(exc_info.value), repr(exc_info.value), caplog.text])
    assert "open positions payload missing required fields" in exposed_text
    for forbidden in (
        "BTCUSDT",
        "not-a-decimal",
        "64000.50",
        "64123.45",
        "16000.125",
        "30.7375",
        "800.00625",
        "80.000625",
        "123456789",
        "accountId",
    ):
        assert forbidden not in exposed_text


def test_open_positions_model_is_documented_as_external_read_only_observation():
    doc = (OpenPositions.__doc__ or "").lower()

    assert "external read-only" in doc
    assert "not internal" in doc


def test_only_approved_read_only_methods_exist_among_client_query_methods():
    client = BybitReadOnlyClient(_settings())

    assert hasattr(client, "get_server_time")
    assert hasattr(client, "get_query_api_info")
    assert hasattr(client, "get_wallet_balance")
    assert hasattr(client, "get_open_positions")
    for forbidden in (
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
