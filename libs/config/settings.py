from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_BYBIT_B1_ALLOWED_ENVIRONMENTS = frozenset({"testnet", "demo"})
_BYBIT_B1_ALLOWED_ENDPOINTS = ("server_time", "wallet_balance", "open_positions")
_BYBIT_B1_FORBIDDEN_ENDPOINTS = frozenset({
    "order_status",
    "place_order",
    "cancel_order",
    "set_leverage",
    "withdraw",
    "transfer",
    "live_reconcile",
    "live_execution",
})


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"
    system_mode: str = "approval"
    paper_mode: bool = True
    execution_mode: str = "paper"
    postgres_dsn: SecretStr
    redis_url: SecretStr
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    telegram_bot_token: SecretStr | None = None
    exchange_api_key: SecretStr | None = None
    exchange_api_secret: SecretStr | None = None

    @field_validator("postgres_dsn", "redis_url")
    @classmethod
    def required_secret_must_exist(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("must be set")
        return v


class BybitB1Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BYBIT_B1_",
        extra="ignore",
        populate_by_name=True,
    )

    exchange: str = "bybit"
    environment: str = "testnet"
    account_type: str = "uta"
    position_mode: str = "one_way"
    leverage_policy: str = "manual_preconfig"
    allowed_endpoints: tuple[str, ...] = _BYBIT_B1_ALLOWED_ENDPOINTS
    api_key: SecretStr | None = Field(
        default=None,
        repr=False,
        exclude=True,
        validation_alias=AliasChoices("BYBIT_API_KEY", "BYBIT_B1_API_KEY"),
    )
    api_secret: SecretStr | None = Field(
        default=None,
        repr=False,
        exclude=True,
        validation_alias=AliasChoices("BYBIT_API_SECRET", "BYBIT_B1_API_SECRET"),
    )

    @field_validator("exchange")
    @classmethod
    def bybit_only(cls, v: str) -> str:
        if v != "bybit":
            raise ValueError("exchange must be bybit")
        return v

    @field_validator("environment")
    @classmethod
    def testnet_or_demo_only(cls, v: str) -> str:
        if v not in _BYBIT_B1_ALLOWED_ENVIRONMENTS:
            raise ValueError("environment must be testnet or demo")
        return v

    @field_validator("account_type")
    @classmethod
    def uta_only(cls, v: str) -> str:
        if v != "uta":
            raise ValueError("account_type must be uta")
        return v

    @field_validator("position_mode")
    @classmethod
    def one_way_only(cls, v: str) -> str:
        if v != "one_way":
            raise ValueError("position_mode must be one_way")
        return v

    @field_validator("leverage_policy")
    @classmethod
    def manual_preconfig_only(cls, v: str) -> str:
        if v != "manual_preconfig":
            raise ValueError("leverage_policy must be manual_preconfig")
        return v

    @field_validator("allowed_endpoints")
    @classmethod
    def first_slice_endpoints_only(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        forbidden = _BYBIT_B1_FORBIDDEN_ENDPOINTS.intersection(v)
        if forbidden:
            raise ValueError(f"forbidden endpoints/actions: {sorted(forbidden)}")
        if v != _BYBIT_B1_ALLOWED_ENDPOINTS:
            raise ValueError(
                "allowed_endpoints must be exactly server_time, wallet_balance, open_positions"
            )
        return v


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_all_configs(config_dir: str | Path = "config") -> dict[str, dict[str, Any]]:
    config_dir = Path(config_dir)
    return {
        "system": load_yaml(config_dir / "system.yaml"),
        "models": load_yaml(config_dir / "models.yaml"),
        "risk": load_yaml(config_dir / "risk.yaml"),
        "exchange": load_yaml(config_dir / "exchange.yaml"),
        "telegram": load_yaml(config_dir / "telegram.yaml"),
        "strategy": load_yaml(config_dir / "strategy.yaml"),
        "logging": load_yaml(config_dir / "logging.yaml"),
        "alerts": load_yaml(config_dir / "alerts.yaml"),
        "feature_flags": load_yaml(config_dir / "feature_flags.yaml"),
    }
