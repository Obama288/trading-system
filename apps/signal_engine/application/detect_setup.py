from __future__ import annotations

from apps.signal_engine.domain.setup_detector import detect_breakout_retest
from libs.schemas.common import EntryZone, MarketSnapshot, TradeDirection


def detect_setup_use_case(snapshot: MarketSnapshot) -> tuple[bool, TradeDirection, EntryZone | None]:
    return detect_breakout_retest(snapshot)
