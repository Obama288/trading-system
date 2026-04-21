from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"
    system_mode: str = "approval"
    paper_mode: bool = True
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
