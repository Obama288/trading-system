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
from libs.exchange.bybit_models import ServerTime
from libs.exchange.errors import (
    ExchangeAuthError,
    ExchangeConfigurationError,
    ExchangeRateLimited,
    ExchangeResponseError,
    MarketDataUnavailable,
)
from scripts import smoke_server_time


FAKE_API_KEY = "testnet_fake_key"
FAKE_API_SECRET = "testnet_fake_secret"
FAKE_B1_KEY = "fake_b1_key"
FAKE_B1_SECRET = "fake_b1_secret"
FAKE_GENERIC_KEY = "fake_generic_key"
FAKE_GENERIC_SECRET = "fake_generic_secret"
FAKE_SIGNATURE = "deadbeefcafebabefeedface1234567890abcdef"
RAW_RET_MSG = "raw retMsg with account_id=123 balance=999 X-BAPI-SIGN=secret"
RAW_BODY = '{"retMsg":"raw response body","api_secret":"secret"}'
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _ClientReturnsServerTime:
    settings: BybitB1Settings

    async def get_server_time(self) -> ServerTime:
        return ServerTime(
            exchange="bybit",
            time_second=1_700_000_000,
            time_nano=1_700_000_000_123_456_789,
        )

    async def get_wallet_balance(self) -> NoReturn:
        raise AssertionError("wallet_balance smoke is not authorized in B2a")

    async def get_open_positions(self) -> NoReturn:
        raise AssertionError("open_positions smoke is not authorized in B2a")


class _ClientRaises:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def get_server_time(self) -> NoReturn:
        raise self._exc


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
        "account_id=123",
        "balance=999",
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
async def test_successful_server_time_output_is_sanitized():
    exit_code, output = await smoke_server_time.run_server_time_smoke(
        settings=_settings(),
        client_factory=_ClientReturnsServerTime,
    )

    assert exit_code == 0
    assert output["operation"] == "bybit_b1_server_time_smoke"
    assert output["endpoint"] == "server_time"
    assert output["endpoint_family"] == "server_time"
    assert output["status"] == "success"
    assert output["exchange"] == "bybit"
    assert output["timestamp_second"] == 1_700_000_000
    assert output["timestamp_nano"] == 1_700_000_000_123_456_789
    assert isinstance(output["elapsed_ms"], int)
    _assert_sanitized(output)


@pytest.mark.asyncio
async def test_missing_credentials_do_not_block_public_server_time_when_client_is_mocked():
    exit_code, output = await smoke_server_time.run_server_time_smoke(
        settings=BybitB1Settings(api_key=None, api_secret=None),
        client_factory=_ClientReturnsServerTime,
    )

    assert exit_code == 0
    assert output["status"] == "success"
    assert output["endpoint"] == "server_time"
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

    exit_code, output = await smoke_server_time.run_server_time_smoke(
        settings=_settings(),
        client_factory=_factory,
    )

    assert exit_code == 1
    assert output["status"] == "failure"
    assert output["error_category"] == "configuration_error"
    _assert_sanitized(output)


@pytest.mark.asyncio
async def test_rate_limit_is_inconclusive_not_success():
    exit_code, output = await smoke_server_time.run_server_time_smoke(
        settings=_settings(),
        client_factory=lambda settings: _ClientRaises(ExchangeRateLimited(RAW_RET_MSG)),
    )

    assert exit_code == 2
    assert output["status"] == "inconclusive"
    assert output["error_category"] == "rate_limited"
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
    exit_code, output = await smoke_server_time.run_server_time_smoke(
        settings=_settings(),
        client_factory=lambda settings: _ClientRaises(exc),
    )

    assert exit_code == 1
    assert output["status"] == "failure"
    assert output["error_category"] == category
    if isinstance(exc, ExchangeResponseError):
        assert output["retCode"] == 0
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

    exit_code, output = await smoke_server_time.run_server_time_smoke(
        settings=_settings(),
        client_factory=lambda settings: _ClientRaises(exc),
    )

    assert exit_code == 1
    assert output["status"] == "failure"
    assert output["error_category"] == category
    assert output["retCode"] == ret_code
    _assert_sanitized(output)


def test_cli_without_authorization_does_not_call_smoke_or_require_credentials(
    monkeypatch,
    capsys,
):
    async def _forbidden_run():
        raise AssertionError("real-capable smoke must not run without explicit authorization")

    def _forbidden_settings(*args, **kwargs):
        raise AssertionError("settings/credentials must not be loaded without authorization")

    monkeypatch.setattr(smoke_server_time, "run_server_time_smoke", _forbidden_run)
    monkeypatch.setattr(smoke_server_time, "BybitB1Settings", _forbidden_settings, raising=False)

    exit_code = smoke_server_time.main([])

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert exit_code == 3
    assert output == {
        "endpoint": "get_server_time",
        "status": "authorization_required",
        "message": "Real smoke execution requires explicit Human Owner authorization.",
        "exit_code": 3,
    }
    _assert_sanitized(output)


def test_direct_cli_without_authorization_exits_3_without_traceback_or_import_error():
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "smoke_server_time.py")],
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
        "endpoint": "get_server_time",
        "status": "authorization_required",
        "message": "Real smoke execution requires explicit Human Owner authorization.",
        "exit_code": 3,
    }
    _assert_sanitized(output)


def test_direct_cli_without_authorization_ignores_fake_bybit_env_aliases():
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "smoke_server_time.py")],
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
            "operation": "bybit_b1_server_time_smoke",
            "endpoint": "server_time",
            "endpoint_family": "server_time",
            "status": "success",
            "exchange": "bybit",
            "timestamp_second": 1,
            "timestamp_nano": 2,
            "elapsed_ms": 3,
        }

    monkeypatch.setattr(smoke_server_time, "run_server_time_smoke", _fake_run)

    exit_code = smoke_server_time.main(["--allow-real-smoke"])

    captured = capsys.readouterr()
    assert exit_code == 0
    output = json.loads(captured.out)
    assert output["endpoint"] == "server_time"
    _assert_sanitized(output)


def test_cli_with_authorization_preserves_rate_limit_inconclusive(monkeypatch, capsys):
    async def _fake_run():
        return 2, {
            "operation": "bybit_b1_server_time_smoke",
            "endpoint": "server_time",
            "endpoint_family": "server_time",
            "status": "inconclusive",
            "error_category": "rate_limited",
            "elapsed_ms": 3,
        }

    monkeypatch.setattr(smoke_server_time, "run_server_time_smoke", _fake_run)

    exit_code = smoke_server_time.main(["--allow-real-smoke"])

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert exit_code == 2
    assert output["status"] == "inconclusive"
    assert output["error_category"] == "rate_limited"
    _assert_sanitized(output)


def test_no_wallet_balance_or_open_positions_smoke_is_implemented():
    assert not hasattr(smoke_server_time, "run_wallet_balance_smoke")
    assert not hasattr(smoke_server_time, "run_open_positions_smoke")
    assert "get_wallet_balance" not in smoke_server_time.__dict__
    assert "get_open_positions" not in smoke_server_time.__dict__
