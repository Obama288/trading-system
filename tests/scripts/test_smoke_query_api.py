from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import pytest
from pydantic import SecretStr, ValidationError

from libs.config.settings import BybitB1Settings
from libs.exchange.bybit_models import ApiKeyInfo
from libs.exchange.errors import (
    ExchangeAuthError,
    ExchangeConfigurationError,
    ExchangeRateLimited,
    ExchangeResponseError,
    MarketDataUnavailable,
)
from scripts import smoke_query_api


FAKE_API_KEY = "testnet_fake_key"
FAKE_API_SECRET = "testnet_fake_secret"
FAKE_B1_KEY = "fake_b1_key"
FAKE_B1_SECRET = "fake_b1_secret"
FAKE_GENERIC_KEY = "fake_generic_key"
FAKE_GENERIC_SECRET = "fake_generic_secret"
FAKE_SIGNATURE = "deadbeefcafebabefeedface1234567890abcdef"
RAW_RET_MSG = "raw retMsg uid=123 ip=192.0.2.1 X-BAPI-SIGN=secret"
RAW_BODY = '{"retMsg":"raw response body","api_secret":"secret","permissions":["Withdraw"]}'
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _ClientReturnsQueryApiInfo:
    settings: BybitB1Settings

    async def get_query_api_info(self) -> ApiKeyInfo:
        return ApiKeyInfo(
            exchange="bybit",
            read_only=True,
            permissions_safe=True,
            key_active=True,
            deadline_days_present=True,
            expired_at_present=False,
        )

    async def get_wallet_balance(self) -> NoReturn:
        raise AssertionError("wallet_balance smoke is not part of B2c.1b query-api")

    async def get_open_positions(self) -> NoReturn:
        raise AssertionError("open_positions smoke is not authorized in B2c.1b")


class _ClientRaises:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def get_query_api_info(self) -> NoReturn:
        raise self._exc

    async def get_wallet_balance(self) -> NoReturn:
        raise AssertionError("wallet_balance smoke is not part of B2c.1b query-api")

    async def get_open_positions(self) -> NoReturn:
        raise AssertionError("open_positions smoke is not authorized in B2c.1b")


def _with_error_metadata(exc: Exception, *, category: str, ret_code: int) -> Exception:
    setattr(exc, "error_category", category)
    setattr(exc, "ret_code", ret_code)
    return exc


def _settings(environment: str = "testnet") -> BybitB1Settings:
    return BybitB1Settings(
        environment=environment,
        api_key=SecretStr(FAKE_API_KEY),
        api_secret=SecretStr(FAKE_API_SECRET),
    )


def _rendered(output: dict) -> str:
    return json.dumps(output, sort_keys=True)


def _assert_sanitized(output: dict) -> None:
    rendered = _rendered(output)
    for forbidden in (
        FAKE_API_KEY,
        FAKE_API_SECRET,
        FAKE_B1_KEY,
        FAKE_B1_SECRET,
        FAKE_GENERIC_KEY,
        FAKE_GENERIC_SECRET,
        FAKE_SIGNATURE,
        "X-BAPI-SIGN",
        "X-BAPI-API-KEY",
        "signed_payload",
        "api_secret",
        "api_key",
        RAW_RET_MSG,
        RAW_BODY,
        "uid=123",
        "userID",
        "accountId",
        "192.0.2.1",
        "Withdraw",
        "Transfer",
        "Order",
        "Trade",
        "walletBalance",
        "positionValue",
        "BTCUSDT",
    ):
        assert forbidden not in rendered


def _env_with_fake_bybit_aliases() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("BYBIT")}
    env.update(
        {
            "BYBIT_B1_ENVIRONMENT": "testnet",
            "BYBIT_B1_API_KEY": FAKE_B1_KEY,
            "BYBIT_B1_API_SECRET": FAKE_B1_SECRET,
            "BYBIT_API_KEY": FAKE_GENERIC_KEY,
            "BYBIT_API_SECRET": FAKE_GENERIC_SECRET,
        }
    )
    return env


@pytest.mark.asyncio
async def test_successful_query_api_output_is_sanitized():
    exit_code, output = await smoke_query_api.run_query_api_smoke(
        settings=_settings(),
        client_factory=_ClientReturnsQueryApiInfo,
    )

    assert exit_code == 0
    assert output == {
        "endpoint": "query_api",
        "status": "success",
        "elapsed_ms": output["elapsed_ms"],
        "exchange": "bybit",
        "read_only": True,
        "permissions_safe": True,
        "key_active": True,
        "deadline_days_present": True,
        "expired_at_present": False,
    }
    assert set(output) == {
        "endpoint",
        "status",
        "exchange",
        "read_only",
        "permissions_safe",
        "key_active",
        "deadline_days_present",
        "expired_at_present",
        "elapsed_ms",
    }
    assert "operation" not in output
    assert "endpoint_family" not in output
    assert isinstance(output["elapsed_ms"], int)
    _assert_sanitized(output)


@pytest.mark.asyncio
async def test_preflight_failure_is_sanitized():
    exc = _with_error_metadata(
        ExchangeAuthError(RAW_RET_MSG),
        category="preflight_failed",
        ret_code=0,
    )

    exit_code, output = await smoke_query_api.run_query_api_smoke(
        settings=_settings(),
        client_factory=lambda settings: _ClientRaises(exc),
    )

    assert exit_code == 1
    assert output["status"] == "failure"
    assert output["error_category"] == "preflight_failed"
    assert output["retCode"] == 0
    _assert_sanitized(output)


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["production", "live"])
async def test_production_and_live_config_rejected(environment: str):
    with pytest.raises(ValidationError):
        BybitB1Settings(
            environment=environment,
            api_key=SecretStr(FAKE_API_KEY),
            api_secret=SecretStr(FAKE_API_SECRET),
        )


@pytest.mark.asyncio
async def test_production_endpoint_rejected_safely():
    def _factory(settings: BybitB1Settings):
        raise ExchangeConfigurationError("production Bybit base URL is forbidden")

    exit_code, output = await smoke_query_api.run_query_api_smoke(
        settings=_settings(),
        client_factory=_factory,
    )

    assert exit_code == 1
    assert output["status"] == "failure"
    assert output["error_category"] == "configuration_error"
    _assert_sanitized(output)


@pytest.mark.asyncio
async def test_rate_limit_is_inconclusive_not_success():
    exc = _with_error_metadata(
        ExchangeRateLimited(RAW_RET_MSG),
        category="rate_limited",
        ret_code=10006,
    )

    exit_code, output = await smoke_query_api.run_query_api_smoke(
        settings=_settings(),
        client_factory=lambda settings: _ClientRaises(exc),
    )

    assert exit_code == 2
    assert output["status"] == "inconclusive"
    assert output["error_category"] == "rate_limited"
    assert output["retCode"] == 10006
    _assert_sanitized(output)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("category", "ret_code"),
    [
        ("timestamp_or_recv_window_error", 10002),
        ("invalid_key_or_environment", 10003),
        ("invalid_signature", 10004),
        ("permission_denied", 10005),
        ("authentication_failed", 10007),
        ("ip_mismatch", 10010),
    ],
)
async def test_granular_bybit_error_categories_are_sanitized(category: str, ret_code: int):
    exc = _with_error_metadata(
        ExchangeAuthError(RAW_RET_MSG),
        category=category,
        ret_code=ret_code,
    )

    exit_code, output = await smoke_query_api.run_query_api_smoke(
        settings=_settings(),
        client_factory=lambda settings: _ClientRaises(exc),
    )

    assert exit_code == 1
    assert output["status"] == "failure"
    assert output["error_category"] == category
    assert output["retCode"] == ret_code
    _assert_sanitized(output)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "category"),
    [
        (ExchangeAuthError(RAW_RET_MSG), "auth_error"),
        (MarketDataUnavailable(RAW_BODY), "network_or_timeout"),
        (ExchangeResponseError(ret_code=0, ret_msg=RAW_RET_MSG), "response_error"),
    ],
)
async def test_failures_are_sanitized(exc: Exception, category: str):
    exit_code, output = await smoke_query_api.run_query_api_smoke(
        settings=_settings(),
        client_factory=lambda settings: _ClientRaises(exc),
    )

    assert exit_code == 1
    assert output["status"] == "failure"
    assert output["error_category"] == category
    if isinstance(exc, ExchangeResponseError):
        assert output["retCode"] == 0
    _assert_sanitized(output)


def test_cli_without_authorization_does_not_call_smoke_or_require_credentials(
    monkeypatch,
    capsys,
):
    async def _forbidden_run():
        raise AssertionError("real-capable smoke must not run without explicit authorization")

    def _forbidden_settings(*args, **kwargs):
        raise AssertionError("settings/credentials must not be loaded without authorization")

    monkeypatch.setattr(smoke_query_api, "run_query_api_smoke", _forbidden_run)
    monkeypatch.setattr(smoke_query_api, "BybitB1Settings", _forbidden_settings, raising=False)

    exit_code = smoke_query_api.main([])

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert exit_code == 3
    assert output == {
        "endpoint": "get_query_api_info",
        "status": "authorization_required",
        "message": "Real smoke execution requires explicit Human Owner authorization.",
        "exit_code": 3,
    }
    _assert_sanitized(output)


def test_direct_cli_without_authorization_exits_3_without_traceback_or_import_error():
    completed = subprocess.run(
        [sys.executable, "scripts\\smoke_query_api.py"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 3
    assert completed.stderr == ""
    assert "Traceback" not in completed.stdout
    assert "ModuleNotFoundError" not in completed.stdout
    output = json.loads(completed.stdout)
    assert output == {
        "endpoint": "get_query_api_info",
        "status": "authorization_required",
        "message": "Real smoke execution requires explicit Human Owner authorization.",
        "exit_code": 3,
    }
    _assert_sanitized(output)


def test_direct_cli_without_authorization_ignores_fake_bybit_env_aliases():
    completed = subprocess.run(
        [sys.executable, "scripts\\smoke_query_api.py"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_env_with_fake_bybit_aliases(),
    )

    assert completed.returncode == 3
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert output["status"] == "authorization_required"
    assert output["exit_code"] == 3
    _assert_sanitized(output)


def test_cli_with_authorization_prints_sanitized_json(monkeypatch, capsys):
    async def _fake_run():
        return 0, {
            "endpoint": "query_api",
            "status": "success",
            "exchange": "bybit",
            "read_only": True,
            "permissions_safe": True,
            "key_active": True,
            "deadline_days_present": True,
            "expired_at_present": False,
            "elapsed_ms": 3,
        }

    monkeypatch.setattr(smoke_query_api, "run_query_api_smoke", _fake_run)

    exit_code = smoke_query_api.main(["--allow-real-smoke"])

    captured = capsys.readouterr()
    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["endpoint"] == "query_api"
    assert output["permissions_safe"] is True
    assert set(output) == {
        "endpoint",
        "status",
        "exchange",
        "read_only",
        "permissions_safe",
        "key_active",
        "deadline_days_present",
        "expired_at_present",
        "elapsed_ms",
    }
    assert "operation" not in output
    assert "endpoint_family" not in output
    _assert_sanitized(output)


def test_cli_with_authorization_preserves_rate_limit_inconclusive(monkeypatch, capsys):
    async def _fake_run():
        return 2, {
            "operation": "bybit_b1_query_api_smoke",
            "endpoint": "query_api",
            "endpoint_family": "query_api",
            "status": "inconclusive",
            "error_category": "rate_limited",
            "retCode": 10006,
            "elapsed_ms": 3,
        }

    monkeypatch.setattr(smoke_query_api, "run_query_api_smoke", _fake_run)

    exit_code = smoke_query_api.main(["--allow-real-smoke"])

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert exit_code == 2
    assert output["status"] == "inconclusive"
    assert output["error_category"] == "rate_limited"
    assert output["retCode"] == 10006
    _assert_sanitized(output)


def test_no_wallet_open_positions_order_status_or_write_live_smoke_is_implemented():
    assert not hasattr(smoke_query_api, "run_wallet_balance_smoke")
    assert not hasattr(smoke_query_api, "run_open_positions_smoke")
    assert not hasattr(smoke_query_api, "run_order_status_smoke")
    assert not hasattr(smoke_query_api, "place_order")
    assert not hasattr(smoke_query_api, "cancel_order")
    assert not hasattr(smoke_query_api, "set_leverage")
    assert not hasattr(smoke_query_api, "withdraw")
    assert not hasattr(smoke_query_api, "transfer")
    assert not hasattr(smoke_query_api, "live_reconcile")
    assert not hasattr(smoke_query_api, "live_execution")
    assert "get_wallet_balance" not in smoke_query_api.__dict__
    assert "get_open_positions" not in smoke_query_api.__dict__
    assert "get_order_status" not in smoke_query_api.__dict__
