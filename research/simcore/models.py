from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"


class FillPolicy(StrEnum):
    NEXT_BAR_OPEN = "next_bar_open"  # default; only gate-eligible policy
    SIGNAL_CLOSE = "signal_close"    # diagnostic-only


@dataclass(frozen=True, slots=True)
class TradeSpec:
    """Immutable specification for a single trade simulation run.

    All numeric fields must be Decimal; floats are rejected with TypeError.
    """

    symbol: str
    direction: Direction
    signal_index: int                     # index of the bar whose CLOSE triggers
    stop_price: Decimal
    target_r_values: tuple[Decimal, ...]  # e.g. (Decimal("1"), Decimal("2"))
    outcome_window_bars: int              # counted from the entry bar, inclusive
    fill: FillPolicy = FillPolicy.NEXT_BAR_OPEN

    def __post_init__(self) -> None:
        if not isinstance(self.stop_price, Decimal):
            raise TypeError(
                f"stop_price must be Decimal, got {type(self.stop_price).__name__}"
            )
        for v in self.target_r_values:
            if not isinstance(v, Decimal):
                raise TypeError(
                    f"target_r_values elements must be Decimal, got {type(v).__name__}"
                )


@dataclass(frozen=True, slots=True)
class TargetSim:
    """Outcome for one target-R level."""

    target_r: Decimal
    target_price: Decimal
    outcome: str          # "win" | "loss" | "flat"
    exit_price: Decimal
    exit_index: int       # absolute candle index
    bars_to_resolution: int  # exit_index - entry_index + 1
    gap_exit: bool        # True when exit came from a bar open beyond level
    final_r_gross: Decimal
    mae_r: Decimal        # maximum adverse excursion over [entry_index..exit_index]
    mfe_r: Decimal        # maximum favourable excursion over [entry_index..exit_index]


@dataclass(frozen=True, slots=True)
class TradeSim:
    """Resolved simulation result for a valid trade."""

    spec: TradeSpec
    entry_index: int
    entry_time: datetime   # decision_time of the signal bar (spec §5.0)
    entry_price: Decimal
    initial_r: Decimal
    session: str           # session label derived from entry_time
    targets: dict[Decimal, TargetSim]

    @property
    def gate_eligible(self) -> bool:
        """True only for NEXT_BAR_OPEN fills (constitution §3.2)."""
        return self.spec.fill == FillPolicy.NEXT_BAR_OPEN


@dataclass(frozen=True, slots=True)
class InvalidTrade:
    """Rejected trade with a machine-readable funnel code."""

    spec: TradeSpec
    reason: str  # see spec §5.1 for valid codes
