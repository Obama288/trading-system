from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, SecretStr

from libs.config.settings import AppSettings, load_all_configs


class JournalReviewConfig(BaseModel):
    service_name: str = "journal-review"
    provider: str
    model: str
    anthropic_api_key: SecretStr | None = None


@lru_cache(maxsize=1)
def get_config() -> JournalReviewConfig:
    settings = AppSettings()
    model_cfg = load_all_configs().get("models", {}).get("journal_review", {})
    return JournalReviewConfig(
        provider=str(model_cfg.get("provider", "anthropic")),
        model=str(model_cfg.get("model", "claude-3-7-sonnet-latest")),
        anthropic_api_key=settings.anthropic_api_key,
    )
