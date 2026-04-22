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


@lru_cache(maxsize=1)
def get_config() -> PositionManagerConfig:
    configs = load_all_configs()
    alerts_cfg = configs.get("alerts", {}).get("alerts", {})
    return PositionManagerConfig(
        journal_service_base_url=os.getenv("JOURNAL_SERVICE_BASE_URL", "http://journal-ingest:8000"),
        alerts_service_base_url=os.getenv("ALERTS_SERVICE_BASE_URL", "http://alerts-service:8000"),
        alerts_enabled=bool(alerts_cfg.get("enabled", True)),
    )
