"""Pure data models for research-layer signal observation collection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum, IntEnum


class SetupId(str, Enum):
    """Supported setup identifiers for SQ_1.0 observations."""

    A = "A"
    B = "B"


class Direction(str, Enum):
    """Signal direction."""

    LONG = "long"
    SHORT = "short"


class ObservationStatus(str, Enum):
    """Observation lifecycle state."""

    CANDIDATE = "candidate"
    VALID = "valid"
    BLOCKED = "blocked"
    RESOLVED = "resolved"


class BtcScore(IntEnum):
    """Allowed BTC context score values for SQ_1.0."""

    BEARISH_BREAKDOWN = -2
    WEAK_REJECTING = -1
    CHOP = 0
    BULLISH_NEAR_RESISTANCE = 1
    BULLISH = 2


def _coerce_setup_id(value: SetupId | str) -> SetupId:
    if isinstance(value, SetupId):
        return value
    try:
        return SetupId(value)
    except ValueError as exc:
        raise ValueError(f"unsupported setup_id: {value!r}") from exc


def _coerce_direction(value: Direction | str) -> Direction:
    if isinstance(value, Direction):
        return value
    try:
        return Direction(value)
    except ValueError as exc:
        raise ValueError(f"unsupported direction: {value!r}") from exc


def _coerce_status(value: ObservationStatus | str) -> ObservationStatus:
    if isinstance(value, ObservationStatus):
        return value
    try:
        return ObservationStatus(value)
    except ValueError as exc:
        raise ValueError(f"unsupported status: {value!r}") from exc


def _coerce_btc_score(value: BtcScore | int) -> BtcScore:
    if isinstance(value, BtcScore):
        return value
    try:
        return BtcScore(value)
    except ValueError as exc:
        raise ValueError(f"unsupported btc_score: {value!r}") from exc


def _ensure_decimal_or_none(name: str, value: Decimal | None) -> None:
    if value is not None and not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal or None")


@dataclass(slots=True, frozen=True)
class OutcomeResult:
    """Resolved or partially resolved R-based outcome summary."""

    outcome_window_candles: int
    mfe_r: Decimal | None = None
    mae_r: Decimal | None = None
    final_r: Decimal | None = None
    hit_target_before_stop: bool = False
    hit_stop_before_target: bool = False
    resolution_reason: str | None = None

    def __post_init__(self) -> None:
        if self.outcome_window_candles <= 0:
            raise ValueError("outcome_window_candles must be positive")
        _ensure_decimal_or_none("mfe_r", self.mfe_r)
        _ensure_decimal_or_none("mae_r", self.mae_r)
        _ensure_decimal_or_none("final_r", self.final_r)


@dataclass(slots=True)
class SignalObservation:
    """Research-layer signal observation record with no execution state."""

    observation_id: str
    created_at_utc: datetime
    source_exchange: str
    symbol: str
    setup_id: SetupId | str
    direction: Direction | str
    context_timeframe: str
    trigger_timeframe: str
    signal_time: datetime
    entry_time_theoretical: datetime | None
    entry_price_theoretical: Decimal | None
    stop_price_theoretical: Decimal | None
    target_price_theoretical: Decimal | None
    initial_r: Decimal | None
    btc_score: BtcScore | int
    session_utc_hour: int
    session_label: str
    status: ObservationStatus | str
    outcome_window_candles: int
    mfe_r: Decimal | None = None
    mae_r: Decimal | None = None
    final_r: Decimal | None = None
    hit_target_before_stop: bool = False
    hit_stop_before_target: bool = False
    resolution_reason: str | None = None

    def __post_init__(self) -> None:
        self.setup_id = _coerce_setup_id(self.setup_id)
        self.direction = _coerce_direction(self.direction)
        self.status = _coerce_status(self.status)
        self.btc_score = _coerce_btc_score(self.btc_score)

        if not self.observation_id:
            raise ValueError("observation_id must not be empty")
        if not self.source_exchange:
            raise ValueError("source_exchange must not be empty")
        if not self.symbol:
            raise ValueError("symbol must not be empty")
        if not self.context_timeframe:
            raise ValueError("context_timeframe must not be empty")
        if not self.trigger_timeframe:
            raise ValueError("trigger_timeframe must not be empty")
        if not self.session_label:
            raise ValueError("session_label must not be empty")
        if not 0 <= self.session_utc_hour <= 23:
            raise ValueError("session_utc_hour must be between 0 and 23")
        if self.outcome_window_candles <= 0:
            raise ValueError("outcome_window_candles must be positive")

        _ensure_decimal_or_none(
            "entry_price_theoretical", self.entry_price_theoretical
        )
        _ensure_decimal_or_none("stop_price_theoretical", self.stop_price_theoretical)
        _ensure_decimal_or_none(
            "target_price_theoretical", self.target_price_theoretical
        )
        _ensure_decimal_or_none("initial_r", self.initial_r)
        _ensure_decimal_or_none("mfe_r", self.mfe_r)
        _ensure_decimal_or_none("mae_r", self.mae_r)
        _ensure_decimal_or_none("final_r", self.final_r)

    @property
    def outcome(self) -> OutcomeResult:
        """Expose outcome-only fields as a nested pure-data view."""

        return OutcomeResult(
            outcome_window_candles=self.outcome_window_candles,
            mfe_r=self.mfe_r,
            mae_r=self.mae_r,
            final_r=self.final_r,
            hit_target_before_stop=self.hit_target_before_stop,
            hit_stop_before_target=self.hit_stop_before_target,
            resolution_reason=self.resolution_reason,
        )
