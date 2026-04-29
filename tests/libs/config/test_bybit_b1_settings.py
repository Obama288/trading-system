from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from libs.config.settings import AppSettings, BybitB1Settings


BYBIT_ENV_NAMES = (
    "BYBIT_B1_ENVIRONMENT",
    "BYBIT_B1_API_KEY",
    "BYBIT_B1_API_SECRET",
    "BYBIT_API_KEY",
    "BYBIT_API_SECRET",
)
FAKE_B1_KEY = "fake_b1_key"
FAKE_B1_SECRET = "fake_b1_secret"
FAKE_GENERIC_KEY = "fake_generic_key"
FAKE_GENERIC_SECRET = "fake_generic_secret"


def test_bybit_b1_settings_safe_defaults():
    settings = BybitB1Settings()

    assert settings.exchange == "bybit"
    assert settings.environment == "testnet"
    assert settings.account_type == "uta"
    assert settings.position_mode == "one_way"
    assert settings.leverage_policy == "manual_preconfig"
    assert settings.allowed_endpoints == ("server_time", "wallet_balance", "open_positions")
    assert settings.api_key is None
    assert settings.api_secret is None


def test_bybit_b1_settings_safe_defaults_when_bybit_env_is_cleared():
    with patch.dict("os.environ", {}, clear=True):
        assert all(name not in os.environ for name in BYBIT_ENV_NAMES)
        settings = BybitB1Settings(_env_file=None)

    assert settings.environment == "testnet"
    assert settings.api_key is None
    assert settings.api_secret is None


def test_bybit_b1_settings_safe_defaults_require_clearing_b1_and_generic_aliases():
    env = {
        "POSTGRES_DSN": "postgresql+psycopg://user:pass@localhost:5432/trading",
        "REDIS_URL": "redis://localhost:6379/0",
    }
    with patch.dict("os.environ", env, clear=True):
        settings = BybitB1Settings(_env_file=None)

    assert settings.environment == "testnet"
    assert settings.api_key is None
    assert settings.api_secret is None


def test_bybit_b1_settings_reads_b1_specific_key_pair_when_only_b1_env_is_set():
    env = {
        "BYBIT_B1_API_KEY": FAKE_B1_KEY,
        "BYBIT_B1_API_SECRET": FAKE_B1_SECRET,
    }
    with patch.dict("os.environ", env, clear=True):
        settings = BybitB1Settings(_env_file=None)

    assert settings.api_key is not None
    assert settings.api_secret is not None
    assert settings.api_key.get_secret_value() == FAKE_B1_KEY
    assert settings.api_secret.get_secret_value() == FAKE_B1_SECRET


def test_bybit_b1_settings_uses_generic_key_pair_only_as_fallback():
    env = {
        "BYBIT_API_KEY": FAKE_GENERIC_KEY,
        "BYBIT_API_SECRET": FAKE_GENERIC_SECRET,
    }
    with patch.dict("os.environ", env, clear=True):
        settings = BybitB1Settings(_env_file=None)

    assert settings.api_key is not None
    assert settings.api_secret is not None
    assert settings.api_key.get_secret_value() == FAKE_GENERIC_KEY
    assert settings.api_secret.get_secret_value() == FAKE_GENERIC_SECRET


def test_bybit_b1_settings_prefers_b1_specific_env_over_generic_aliases():
    env = {
        "BYBIT_B1_API_KEY": FAKE_B1_KEY,
        "BYBIT_B1_API_SECRET": FAKE_B1_SECRET,
        "BYBIT_API_KEY": FAKE_GENERIC_KEY,
        "BYBIT_API_SECRET": FAKE_GENERIC_SECRET,
    }
    with patch.dict("os.environ", env, clear=True):
        settings = BybitB1Settings(_env_file=None)

    assert settings.api_key is not None
    assert settings.api_secret is not None
    assert settings.api_key.get_secret_value() == FAKE_B1_KEY
    assert settings.api_secret.get_secret_value() == FAKE_B1_SECRET


@pytest.mark.parametrize("environment", ["testnet", "demo"])
def test_bybit_b1_settings_allows_testnet_and_demo(environment: str):
    assert BybitB1Settings(environment=environment).environment == environment


@pytest.mark.parametrize("environment", ["production", "live"])
def test_bybit_b1_settings_rejects_production_and_live(environment: str):
    with pytest.raises(ValidationError):
        BybitB1Settings(environment=environment)


def test_bybit_b1_settings_account_type_default_is_uta():
    assert BybitB1Settings().account_type == "uta"


def test_bybit_b1_settings_position_mode_default_is_one_way():
    assert BybitB1Settings().position_mode == "one_way"


def test_bybit_b1_settings_leverage_policy_default_is_manual_preconfig():
    assert BybitB1Settings().leverage_policy == "manual_preconfig"


def test_bybit_b1_settings_allowed_endpoints_default_exactly_first_slice():
    assert BybitB1Settings().allowed_endpoints == (
        "server_time",
        "wallet_balance",
        "open_positions",
    )


@pytest.mark.parametrize(
    "forbidden",
    [
        "order_status",
        "place_order",
        "cancel_order",
        "set_leverage",
        "withdraw",
        "transfer",
        "live_reconcile",
        "live_execution",
    ],
)
def test_bybit_b1_settings_rejects_forbidden_endpoints_and_actions(forbidden: str):
    with pytest.raises(ValidationError):
        BybitB1Settings(
            allowed_endpoints=(
                "server_time",
                "wallet_balance",
                "open_positions",
                forbidden,
            )
        )


def test_bybit_b1_settings_secret_fields_are_secretstr_and_do_not_leak():
    settings = BybitB1Settings(
        api_key="testnet-key-value",
        api_secret="testnet-secret-value",
    )

    assert isinstance(settings.api_key, SecretStr)
    assert isinstance(settings.api_secret, SecretStr)
    assert settings.api_key.get_secret_value() == "testnet-key-value"
    assert settings.api_secret.get_secret_value() == "testnet-secret-value"

    rendered = repr(settings)
    dumped = str(settings.model_dump())
    assert "testnet-key-value" not in rendered
    assert "testnet-secret-value" not in rendered
    assert "testnet-key-value" not in dumped
    assert "testnet-secret-value" not in dumped
    assert "api_key" not in dumped
    assert "api_secret" not in dumped


def test_missing_bybit_b1_secrets_do_not_break_app_settings_import_or_startup():
    env = {
        "POSTGRES_DSN": "postgresql+psycopg://user:pass@localhost:5432/trading",
        "REDIS_URL": "redis://localhost:6379/0",
    }
    with patch.dict("os.environ", env, clear=True):
        settings = AppSettings()

    assert settings.postgres_dsn.get_secret_value() == env["POSTGRES_DSN"]
    assert settings.redis_url.get_secret_value() == env["REDIS_URL"]
