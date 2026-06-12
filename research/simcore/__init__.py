"""Unified outcome simulator — public API (spec §2)."""

from research.simcore.candles import Candle, normalize_utc, parse_iso_utc
from research.simcore.costs import SCENARIOS, cost_in_r, final_r_net
from research.simcore.models import (
    Direction,
    FillPolicy,
    InvalidTrade,
    TargetSim,
    TradeSim,
    TradeSpec,
)
from research.simcore.selection import select_non_overlapping
from research.simcore.simulator import simulate_multi_target, simulate_trade
from research.simcore.timeutil import bar_duration, decision_time, label_session

__all__ = [
    "Candle",
    "normalize_utc",
    "parse_iso_utc",
    "Direction",
    "FillPolicy",
    "TradeSpec",
    "TargetSim",
    "TradeSim",
    "InvalidTrade",
    "simulate_trade",
    "simulate_multi_target",
    "select_non_overlapping",
    "cost_in_r",
    "final_r_net",
    "SCENARIOS",
    "bar_duration",
    "decision_time",
    "label_session",
]
