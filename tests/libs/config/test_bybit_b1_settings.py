from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from libs.config.settings import AppSettings, BybitB1Settings


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
