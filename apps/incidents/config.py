from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class IncidentsConfig(BaseModel):
    service_name: str = "incidents"
    journal_service_base_url: str = "http://journal-ingest:8000"


@lru_cache(maxsize=1)
def get_config() -> IncidentsConfig:
    return IncidentsConfig(
        journal_service_base_url=os.getenv("JOURNAL_SERVICE_BASE_URL", "http://journal-ingest:8000"),
    )
