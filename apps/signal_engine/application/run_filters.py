from __future__ import annotations

from apps.signal_engine.domain.filters import basic_market_filters
from libs.schemas.common import FilterReason, MarketSnapshot


def run_filters_use_case(snapshot: MarketSnapshot) -> tuple[bool, list[FilterReason]]:
    return basic_market_filters(snapshot)
