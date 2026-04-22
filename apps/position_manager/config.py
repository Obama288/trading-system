from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel

from libs.config.settings import load_all_configs


class PositionManagerConfig(BaseModel):
    service_name: str = "position-manager"
    journal_service_base_url: str = "http://journal-ingest:8000"
    alerts_service_base_url: str = "http://alerts-service:8000"
    alerts_enabled: bool = True
    execution_mode: str = "paper"
    reconcile_scheduler_enabled: bool = False
    reconcile_scheduler_interval_seconds: float = 30.0
    reconcile_scheduler_timeframe: str = "1m"
    reconcile_scheduler_candle_limit: int = 2
    reconcile_scheduler_continue_on_error: bool = False


@lru_cache(maxsize=1)
def get_config() -> PositionManagerConfig:
    configs = load_all_configs()
    alerts_cfg = configs.get("alerts", {}).get("alerts", {})

    def env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    return PositionManagerConfig(
        journal_service_base_url=os.getenv("JOURNAL_SERVICE_BASE_URL", "http://journal-ingest:8000"),
        alerts_service_base_url=os.getenv("ALERTS_SERVICE_BASE_URL", "http://alerts-service:8000"),
        alerts_enabled=env_bool("ALERTS_ENABLED", bool(alerts_cfg.get("enabled", True))),
        execution_mode=os.getenv("EXECUTION_MODE", "paper"),
        reconcile_scheduler_enabled=env_bool("POSITION_RECONCILE_SCHEDULER_ENABLED", False),
        reconcile_scheduler_interval_seconds=float(os.getenv("POSITION_RECONCILE_INTERVAL_SECONDS", "30")),
        reconcile_scheduler_timeframe=os.getenv("POSITION_RECONCILE_TIMEFRAME", "1m"),
        reconcile_scheduler_candle_limit=int(os.getenv("POSITION_RECONCILE_CANDLE_LIMIT", "2")),
        reconcile_scheduler_continue_on_error=env_bool("POSITION_RECONCILE_CONTINUE_ON_ERROR", False),
    )
