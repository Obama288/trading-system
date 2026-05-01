from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from libs.config.settings import BitgetBg1Settings


BITGET_ENV_NAMES = (
    "BITGET_BG1_ENVIRONMENT",
    "BITGET_BG1_API_KEY",
    "BITGET_BG1_API_SECRET",
    "BITGET_BG1_PASSPHRASE",
)
UNRELATED_ENV_NAMES = (
    "BYBIT_B1_ENVIRONMENT",
    "BYBIT_B1_API_KEY",
    "BYBIT_B1_API_SECRET",
    "BYBIT_API_KEY",
    "BYBIT_API_SECRET",
)
FAKE_BG1_KEY = "fake_bg1_key"
FAKE_BG1_SECRET = "fake_bg1_secret"
FAKE_BG1_PASSPHRASE = "fake_bg1_passphrase"


def test_bitget_bg1_settings_safe_defaults():
    with patch.dict("os.environ", {}, clear=True):
        settings = BitgetBg1Settings(_env_file=None)

    assert settings.exchange == "bitget"
    assert settings.environment == "demo"
    assert settings.api_key is None
    assert settings.api_secret is None
    assert settings.passphrase is None


def test_bitget_bg1_settings_reads_bg1_specific_env_vars_only():
    env = {
        "BITGET_BG1_ENVIRONMENT": "simulated",
        "BITGET_BG1_API_KEY": FAKE_BG1_KEY,
        "BITGET_BG1_API_SECRET": FAKE_BG1_SECRET,
        "BITGET_BG1_PASSPHRASE": FAKE_BG1_PASSPHRASE,
    }
    with patch.dict("os.environ", env, clear=True):
        settings = BitgetBg1Settings(_env_file=None)

    assert settings.environment == "simulated"
    assert settings.api_key is not None
    assert settings.api_secret is not None
    assert settings.passphrase is not None
    assert settings.api_key.get_secret_value() == FAKE_BG1_KEY
    assert settings.api_secret.get_secret_value() == FAKE_BG1_SECRET
    assert settings.passphrase.get_secret_value() == FAKE_BG1_PASSPHRASE


def test_bitget_bg1_settings_isolated_from_unrelated_env_vars():
    env = {
        "BYBIT_B1_ENVIRONMENT": "testnet",
        "BYBIT_B1_API_KEY": "fake_bybit_b1_key",
        "BYBIT_B1_API_SECRET": "fake_bybit_b1_secret",
        "BYBIT_API_KEY": "fake_bybit_key",
        "BYBIT_API_SECRET": "fake_bybit_secret",
    }
    with patch.dict("os.environ", env, clear=True):
        assert all(name not in os.environ for name in BITGET_ENV_NAMES)
        settings = BitgetBg1Settings(_env_file=None)

    assert settings.environment == "demo"
    assert settings.api_key is None
    assert settings.api_secret is None
    assert settings.passphrase is None


@pytest.mark.parametrize("environment", ["demo", "simulated"])
def test_bitget_bg1_settings_allows_demo_and_simulated(environment: str):
    with patch.dict("os.environ", {}, clear=True):
        assert BitgetBg1Settings(environment=environment, _env_file=None).environment == environment


@pytest.mark.parametrize("environment", ["testnet", "production", "mainnet", "live"])
def test_bitget_bg1_settings_rejects_non_bg1_environments(environment: str):
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValidationError):
            BitgetBg1Settings(environment=environment, _env_file=None)


def test_bitget_bg1_settings_secret_fields_are_secretstr_and_do_not_leak():
    with patch.dict("os.environ", {}, clear=True):
        settings = BitgetBg1Settings(
            api_key="demo-key-value",
            api_secret="demo-secret-value",
            passphrase="demo-passphrase-value",
            _env_file=None,
        )

    assert isinstance(settings.api_key, SecretStr)
    assert isinstance(settings.api_secret, SecretStr)
    assert isinstance(settings.passphrase, SecretStr)
    assert settings.api_key.get_secret_value() == "demo-key-value"
    assert settings.api_secret.get_secret_value() == "demo-secret-value"
    assert settings.passphrase.get_secret_value() == "demo-passphrase-value"

    rendered = repr(settings)
    dumped = str(settings.model_dump())
    for secret_value in (
        "demo-key-value",
        "demo-secret-value",
        "demo-passphrase-value",
    ):
        assert secret_value not in rendered
        assert secret_value not in dumped
    assert "api_key" not in dumped
    assert "api_secret" not in dumped
    assert "passphrase" not in dumped


def test_bitget_bg1_settings_do_not_use_bybit_aliases():
    env = {
        "BITGET_BG1_API_KEY": FAKE_BG1_KEY,
        "BITGET_BG1_API_SECRET": FAKE_BG1_SECRET,
        "BITGET_BG1_PASSPHRASE": FAKE_BG1_PASSPHRASE,
        "BYBIT_B1_API_KEY": "fake_bybit_b1_key",
        "BYBIT_B1_API_SECRET": "fake_bybit_b1_secret",
        "BYBIT_API_KEY": "fake_bybit_key",
        "BYBIT_API_SECRET": "fake_bybit_secret",
    }
    with patch.dict("os.environ", env, clear=True):
        settings = BitgetBg1Settings(_env_file=None)

    assert settings.api_key is not None
    assert settings.api_secret is not None
    assert settings.passphrase is not None
    assert settings.api_key.get_secret_value() == FAKE_BG1_KEY
    assert settings.api_secret.get_secret_value() == FAKE_BG1_SECRET
    assert settings.passphrase.get_secret_value() == FAKE_BG1_PASSPHRASE


def test_bitget_bg1_settings_ignore_unrelated_env_names_without_side_effects():
    env = {
        "POSTGRES_DSN": "postgresql+psycopg://user:pass@localhost:5432/trading",
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "fake_openai_key",
        "BYBIT_B1_API_KEY": "fake_bybit_b1_key",
    }
    with patch.dict("os.environ", env, clear=True):
        settings = BitgetBg1Settings(_env_file=None)

    assert settings.environment == "demo"
    assert settings.api_key is None
    assert settings.api_secret is None
    assert settings.passphrase is None
    assert all(name not in BITGET_ENV_NAMES or name not in env for name in BITGET_ENV_NAMES)
    assert all(name in env for name in ("POSTGRES_DSN", "REDIS_URL", "OPENAI_API_KEY"))
    assert all(name in UNRELATED_ENV_NAMES or name not in BITGET_ENV_NAMES for name in UNRELATED_ENV_NAMES)
