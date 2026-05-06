"""Research-layer signal observation models, loaders, and helpers."""

from .candles import Candle
from .csv_loader import load_ohlcv_csv
from .indicators import atr, ema, pivot_highs, pivot_lows, true_range
from .models import (
    BtcScore,
    Direction,
    ObservationStatus,
    OutcomeResult,
    SetupId,
    SignalObservation,
)
from .outcomes import resolve_outcome
from .sessions import session_label
from .setup_a import detect_setup_a
from .summary import SummaryMetrics, summarize_outcomes

__all__ = [
    "atr",
    "BtcScore",
    "Candle",
    "Direction",
    "detect_setup_a",
    "ema",
    "load_ohlcv_csv",
    "ObservationStatus",
    "OutcomeResult",
    "pivot_highs",
    "pivot_lows",
    "resolve_outcome",
    "SetupId",
    "SignalObservation",
    "session_label",
    "summarize_outcomes",
    "SummaryMetrics",
    "true_range",
]
