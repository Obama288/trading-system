"""Setup B detector for research-layer signal observation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Sequence

from .candles import Candle
from .indicators import atr, pivot_highs, pivot_lows
from research.simcore.models import (
    Direction as _SimDirection,
    FillPolicy as _FillPolicy,
    InvalidTrade as _SimInvalidTrade,
    TradeSpec as _TradeSpec,
)
from research.simcore.simulator import simulate_trade as _simulate_trade


SETUP_NAME = "Trend Pullback BOS / Continuation"
TIMEFRAME = "4H"
PIVOT_LEFT = 2
PIVOT_RIGHT = 2
MIN_PULLBACK_CANDLES = 3
MAX_PULLBACK_CANDLES = 20
MIN_PULLBACK_DEPTH = Decimal("0.30")
MAX_PULLBACK_DEPTH = Decimal("0.70")
OUTCOME_WINDOW_CANDLES = 10
VOLUME_LOOKBACK = 20
PERCENT_BUFFER = Decimal("0.005")
TARGET_R_VALUES = (Decimal("1"), Decimal("1.5"), Decimal("2"))

_BAR_DUR = timedelta(hours=4)  # hardcoded for Setup B; new families must use timeutil.bar_duration


class SignalDirection(str, Enum):
    """Setup B signal direction."""

    LONG = "long"
    SHORT = "short"


class PivotKind(str, Enum):
    """Supported pivot kind."""

    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class Pivot:
    """Confirmed pivot with its original and confirmation indexes."""

    kind: PivotKind
    index: int
    confirmation_index: int
    timestamp: datetime
    confirmation_time: datetime
    price: Decimal


@dataclass(frozen=True, slots=True)
class SetupBObservation:
    """Setup B research observation with no execution state."""

    setup_name: str
    symbol: str
    timeframe: str
    trend_direction: str
    signal_direction: SignalDirection
    signal_time: datetime
    signal_hour_utc: int
    session_label: str
    entry_time: datetime
    entry_price: Decimal
    signal_close: Decimal     # BOS candle close — diagnostic; entry moved to next-bar-open
    next_bar_open: Decimal | None
    stop: Decimal
    target_1r: Decimal
    target_1_5r: Decimal
    target_2r: Decimal
    percent_buffer: Decimal
    atr_buffer: Decimal
    chosen_buffer: Decimal
    pullback_start_time: datetime
    pullback_end_time: datetime
    bos_time: datetime
    trend_age_swings: int
    pullback_depth: Decimal
    pullback_duration: int
    bos_body_ratio: Decimal | None
    bos_volume_ratio: Decimal | None
    atr_at_entry: Decimal
    prior_swing_high: Decimal
    prior_swing_low: Decimal
    impulse_size: Decimal
    mae_1r: Decimal | None
    mfe_1r: Decimal | None
    outcome_1r: str
    bars_to_resolution_1r: int | None
    mae_1_5r: Decimal | None
    mfe_1_5r: Decimal | None
    outcome_1_5r: str
    bars_to_resolution_1_5r: int | None
    mae_2r: Decimal | None
    mfe_2r: Decimal | None
    outcome_2r: str
    bars_to_resolution_2r: int | None


@dataclass(slots=True)
class SetupBCounters:
    """Mutable funnel counters for one symbol/direction run."""

    candles_loaded: int = 0
    windows_checked: int = 0
    pivots_detected: int = 0
    trend_detected: int = 0
    pullback_candidates: int = 0
    valid_pullbacks: int = 0
    pullback_invalidated_before_bos: int = 0
    bos_candidates: int = 0
    bos_confirmed: int = 0
    entry_observations: int = 0
    resolved_1r: int = 0
    wins_1r: int = 0
    losses_1r: int = 0
    flats_1r: int = 0
    resolved_1_5r: int = 0
    wins_1_5r: int = 0
    losses_1_5r: int = 0
    flats_1_5r: int = 0
    resolved_2r: int = 0
    wins_2r: int = 0
    losses_2r: int = 0
    flats_2r: int = 0
    invalid_trade_reasons: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SetupBDetectionResult:
    """Detector result plus diagnostics for one symbol/direction."""

    symbol: str
    direction: SignalDirection
    observations: list[SetupBObservation]
    counters: SetupBCounters
    failures_by_reason: dict[str, int]


def find_pivots(
    candles: Sequence[Candle],
    *,
    left: int = PIVOT_LEFT,
    right: int = PIVOT_RIGHT,
) -> list[Pivot]:
    """Find strict confirmed pivots."""

    high_markers = pivot_highs(candles, left=left, right=right)
    low_markers = pivot_lows(candles, left=left, right=right)
    pivots: list[Pivot] = []
    for index, candle in enumerate(candles):
        confirmation_index = index + right
        if confirmation_index >= len(candles):
            continue
        confirmation_time = candles[confirmation_index].timestamp
        if high_markers[index]:
            pivots.append(
                Pivot(
                    kind=PivotKind.HIGH,
                    index=index,
                    confirmation_index=confirmation_index,
                    timestamp=candle.timestamp,
                    confirmation_time=confirmation_time,
                    price=candle.high,
                )
            )
        if low_markers[index]:
            pivots.append(
                Pivot(
                    kind=PivotKind.LOW,
                    index=index,
                    confirmation_index=confirmation_index,
                    timestamp=candle.timestamp,
                    confirmation_time=confirmation_time,
                    price=candle.low,
                )
            )
    return sorted(pivots, key=lambda pivot: (pivot.index, pivot.kind.value))


def determine_trend_state(
    pivots: Sequence[Pivot],
    *,
    current_index: int,
) -> str | None:
    """Return uptrend/downtrend when the last confirmed pivots prove structure."""

    confirmed = [pivot for pivot in pivots if pivot.confirmation_index <= current_index]
    highs = [pivot for pivot in confirmed if pivot.kind is PivotKind.HIGH]
    lows = [pivot for pivot in confirmed if pivot.kind is PivotKind.LOW]
    if len(highs) < 2 or len(lows) < 2:
        return None

    last_highs = highs[-2:]
    last_lows = lows[-2:]
    if last_highs[1].price > last_highs[0].price and last_lows[1].price > last_lows[0].price:
        return "uptrend"
    if last_highs[1].price < last_highs[0].price and last_lows[1].price < last_lows[0].price:
        return "downtrend"
    return None


def detect_setup_b(
    candles_4h: Sequence[Candle],
    *,
    symbol: str,
    direction: SignalDirection,
) -> list[SetupBObservation]:
    """Detect Setup B observations from local 4H candles only."""

    return detect_setup_b_with_diagnostics(
        candles_4h,
        symbol=symbol,
        direction=direction,
    ).observations


def detect_setup_b_with_diagnostics(
    candles_4h: Sequence[Candle],
    *,
    symbol: str,
    direction: SignalDirection,
) -> SetupBDetectionResult:
    """Detect Setup B observations and produce funnel diagnostics."""

    if not symbol:
        raise ValueError("symbol must not be empty")
    if not isinstance(direction, SignalDirection):
        direction = SignalDirection(direction)

    counters = SetupBCounters(candles_loaded=len(candles_4h))
    failures: dict[str, int] = {}
    observations: list[SetupBObservation] = []

    if not candles_4h:
        return SetupBDetectionResult(symbol, direction, observations, counters, failures)

    pivots = find_pivots(candles_4h)
    counters.pivots_detected = len(pivots)
    atr_values = atr(candles_4h, period=14)
    swing_pivots = _swing_pivots_for_direction(pivots, direction)

    for swing in swing_pivots:
        trend = determine_trend_state(pivots, current_index=swing.confirmation_index)
        expected_trend = "uptrend" if direction is SignalDirection.LONG else "downtrend"
        if trend != expected_trend:
            _increment(failures, "no_structural_trend")
            continue

        counters.trend_detected += 1
        prior_opposite = _previous_opposite_pivot(pivots, swing, direction)
        if prior_opposite is None:
            _increment(failures, "insufficient_confirmed_pivots")
            continue

        impulse_size = _impulse_size(swing, prior_opposite, direction)
        if impulse_size <= Decimal("0"):
            _increment(failures, "invalid_impulse")
            continue

        start = swing.index + 1
        end_limit = min(len(candles_4h), start + MAX_PULLBACK_CANDLES + 1)
        for bos_index in range(start + MIN_PULLBACK_CANDLES, end_limit):
            counters.windows_checked += 1
            pullback = candles_4h[start:bos_index]
            if len(pullback) < MIN_PULLBACK_CANDLES:
                _increment(failures, "pullback_too_short")
                continue
            counters.pullback_candidates += 1

            invalid_reason = _pullback_invalid_reason(
                pullback=pullback,
                swing=swing,
                prior_opposite=prior_opposite,
                impulse_size=impulse_size,
                direction=direction,
            )
            if invalid_reason is not None:
                _increment(failures, invalid_reason)
                if invalid_reason in {
                    "pullback_too_shallow",
                    "pullback_too_deep",
                    "prior_structure_broken",
                }:
                    counters.pullback_invalidated_before_bos += 1
                continue

            counters.valid_pullbacks += 1
            bos_candle = candles_4h[bos_index]
            pullback_high = max(candle.high for candle in pullback)
            pullback_low = min(candle.low for candle in pullback)
            wick_only = _is_wick_only_bos(bos_candle, pullback_high, pullback_low, direction)
            if wick_only:
                counters.bos_candidates += 1
                _increment(failures, "wick_only_bos")
                continue
            if not _is_confirmed_bos(bos_candle, pullback_high, pullback_low, direction):
                _increment(failures, "bos_missing")
                continue

            counters.bos_candidates += 1
            counters.bos_confirmed += 1
            observation = _build_observation(
                candles=candles_4h,
                atr_values=atr_values,
                pivots=pivots,
                symbol=symbol,
                direction=direction,
                swing=swing,
                prior_opposite=prior_opposite,
                pullback=pullback,
                bos_index=bos_index,
                impulse_size=impulse_size,
            )
            if isinstance(observation, _SimInvalidTrade):
                _increment(failures, "stop_invalid_or_non_structural")
                _increment(counters.invalid_trade_reasons, observation.reason)
                continue
            if observation is None:
                _increment(failures, "stop_invalid_or_non_structural")
                continue
            observations.append(observation)
            counters.entry_observations += 1
            _add_outcome_counts(counters, observation)
            break

    return SetupBDetectionResult(symbol, direction, observations, counters, failures)


def _build_observation(
    *,
    candles: Sequence[Candle],
    atr_values: Sequence[Decimal | None],
    pivots: Sequence[Pivot],
    symbol: str,
    direction: SignalDirection,
    swing: Pivot,
    prior_opposite: Pivot,
    pullback: Sequence[Candle],
    bos_index: int,
    impulse_size: Decimal,
) -> SetupBObservation | _SimInvalidTrade | None:
    bos_candle = candles[bos_index]
    atr_at_entry = atr_values[bos_index]
    if atr_at_entry is None:
        return None

    signal_close = bos_candle.close  # diagnostic: BOS candle close (pre-migration entry)
    percent_buffer, atr_buffer, chosen_buffer = calculate_stop_buffer(
        entry_price=signal_close,
        atr_at_entry=atr_at_entry,
    )
    pullback_high = max(candle.high for candle in pullback)
    pullback_low = min(candle.low for candle in pullback)

    if direction is SignalDirection.LONG:
        stop = pullback_low - chosen_buffer
        prior_swing_high = swing.price
        prior_swing_low = prior_opposite.price
        trend_direction = "uptrend"
        pullback_depth = (swing.price - pullback_low) / impulse_size
        sim_direction = _SimDirection.LONG
    else:
        stop = pullback_high + chosen_buffer
        prior_swing_high = prior_opposite.price
        prior_swing_low = swing.price
        trend_direction = "downtrend"
        pullback_depth = (pullback_high - swing.price) / impulse_size
        sim_direction = _SimDirection.SHORT

    spec = _TradeSpec(
        symbol=symbol,
        direction=sim_direction,
        signal_index=bos_index,
        stop_price=stop,
        target_r_values=TARGET_R_VALUES,
        outcome_window_bars=OUTCOME_WINDOW_CANDLES,
        fill=_FillPolicy.NEXT_BAR_OPEN,
    )
    sim_result = _simulate_trade(list(candles), spec, _BAR_DUR)
    if isinstance(sim_result, _SimInvalidTrade):
        return sim_result  # caller records reason in counters.invalid_trade_reasons
    sim = sim_result

    signal_time = sim.entry_time
    entry_price = sim.entry_price
    outcome_1 = sim.targets[Decimal("1")]
    outcome_1_5 = sim.targets[Decimal("1.5")]
    outcome_2 = sim.targets[Decimal("2")]

    return SetupBObservation(
        setup_name=SETUP_NAME,
        symbol=symbol,
        timeframe=TIMEFRAME,
        trend_direction=trend_direction,
        signal_direction=direction,
        signal_time=signal_time,
        signal_hour_utc=signal_time.hour,
        session_label=sim.session,
        entry_time=signal_time,
        entry_price=entry_price,
        signal_close=signal_close,
        next_bar_open=entry_price,
        stop=stop,
        target_1r=outcome_1.target_price,
        target_1_5r=outcome_1_5.target_price,
        target_2r=outcome_2.target_price,
        percent_buffer=percent_buffer,
        atr_buffer=atr_buffer,
        chosen_buffer=chosen_buffer,
        pullback_start_time=pullback[0].timestamp,
        pullback_end_time=pullback[-1].timestamp,
        bos_time=signal_time,
        trend_age_swings=_trend_age_swings(pivots, swing),
        pullback_depth=pullback_depth,
        pullback_duration=len(pullback),
        bos_body_ratio=_body_ratio(bos_candle),
        bos_volume_ratio=_volume_ratio(candles, bos_index),
        atr_at_entry=atr_at_entry,
        prior_swing_high=prior_swing_high,
        prior_swing_low=prior_swing_low,
        impulse_size=impulse_size,
        mae_1r=outcome_1.mae_r,
        mfe_1r=outcome_1.mfe_r,
        outcome_1r=outcome_1.outcome,
        bars_to_resolution_1r=outcome_1.bars_to_resolution,
        mae_1_5r=outcome_1_5.mae_r,
        mfe_1_5r=outcome_1_5.mfe_r,
        outcome_1_5r=outcome_1_5.outcome,
        bars_to_resolution_1_5r=outcome_1_5.bars_to_resolution,
        mae_2r=outcome_2.mae_r,
        mfe_2r=outcome_2.mfe_r,
        outcome_2r=outcome_2.outcome,
        bars_to_resolution_2r=outcome_2.bars_to_resolution,
    )


def calculate_stop_buffer(
    *,
    entry_price: Decimal,
    atr_at_entry: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return percent, ATR, and chosen stop buffer for Setup B."""

    percent_buffer = entry_price * PERCENT_BUFFER
    atr_buffer = atr_at_entry
    return percent_buffer, atr_buffer, min(percent_buffer, atr_buffer)


def is_pullback_depth_valid(depth: Decimal) -> bool:
    """Return whether pullback depth is inside the SQ_B_1.0 range."""

    return MIN_PULLBACK_DEPTH <= depth <= MAX_PULLBACK_DEPTH


def _swing_pivots_for_direction(
    pivots: Sequence[Pivot],
    direction: SignalDirection,
) -> list[Pivot]:
    kind = PivotKind.HIGH if direction is SignalDirection.LONG else PivotKind.LOW
    return [pivot for pivot in pivots if pivot.kind is kind]


def _previous_opposite_pivot(
    pivots: Sequence[Pivot],
    swing: Pivot,
    direction: SignalDirection,
) -> Pivot | None:
    opposite_kind = PivotKind.LOW if direction is SignalDirection.LONG else PivotKind.HIGH
    candidates = [
        pivot
        for pivot in pivots
        if pivot.kind is opposite_kind and pivot.confirmation_index <= swing.confirmation_index
    ]
    if not candidates:
        return None
    return candidates[-1]


def _impulse_size(
    swing: Pivot,
    prior_opposite: Pivot,
    direction: SignalDirection,
) -> Decimal:
    if direction is SignalDirection.LONG:
        return swing.price - prior_opposite.price
    return prior_opposite.price - swing.price


def _pullback_invalid_reason(
    *,
    pullback: Sequence[Candle],
    swing: Pivot,
    prior_opposite: Pivot,
    impulse_size: Decimal,
    direction: SignalDirection,
) -> str | None:
    if len(pullback) < MIN_PULLBACK_CANDLES:
        return "pullback_too_short"
    if direction is SignalDirection.LONG:
        pullback_low = min(candle.low for candle in pullback)
        if pullback_low <= prior_opposite.price:
            return "prior_structure_broken"
        depth = (swing.price - pullback_low) / impulse_size
    else:
        pullback_high = max(candle.high for candle in pullback)
        if pullback_high >= prior_opposite.price:
            return "prior_structure_broken"
        depth = (pullback_high - swing.price) / impulse_size
    if depth < MIN_PULLBACK_DEPTH:
        return "pullback_too_shallow"
    if depth > MAX_PULLBACK_DEPTH:
        return "pullback_too_deep"
    return None


def _is_wick_only_bos(
    candle: Candle,
    pullback_high: Decimal,
    pullback_low: Decimal,
    direction: SignalDirection,
) -> bool:
    if direction is SignalDirection.LONG:
        return candle.high > pullback_high and candle.close <= pullback_high
    return candle.low < pullback_low and candle.close >= pullback_low


def _is_confirmed_bos(
    candle: Candle,
    pullback_high: Decimal,
    pullback_low: Decimal,
    direction: SignalDirection,
) -> bool:
    if direction is SignalDirection.LONG:
        return candle.close > pullback_high
    return candle.close < pullback_low


def _body_ratio(candle: Candle) -> Decimal | None:
    candle_range = candle.high - candle.low
    if candle_range <= Decimal("0"):
        return None
    return abs(candle.close - candle.open) / candle_range


def _volume_ratio(candles: Sequence[Candle], index: int) -> Decimal | None:
    if index < VOLUME_LOOKBACK:
        return None
    average_volume = (
        sum(candle.volume for candle in candles[index - VOLUME_LOOKBACK : index])
        / Decimal(VOLUME_LOOKBACK)
    )
    if average_volume == Decimal("0"):
        return None
    return candles[index].volume / average_volume


def _trend_age_swings(pivots: Sequence[Pivot], swing: Pivot) -> int:
    confirmed = [
        pivot
        for pivot in pivots
        if pivot.confirmation_index <= swing.confirmation_index and pivot.index <= swing.index
    ]
    highs = [pivot for pivot in confirmed if pivot.kind is PivotKind.HIGH]
    lows = [pivot for pivot in confirmed if pivot.kind is PivotKind.LOW]
    if len(highs) < 2 or len(lows) < 2:
        return len(confirmed)
    trend_start_index = min(highs[-2].index, lows[-2].index)
    return sum(1 for pivot in confirmed if pivot.index >= trend_start_index)


def _add_outcome_counts(counters: SetupBCounters, observation: SetupBObservation) -> None:
    _add_single_outcome_counts(
        outcome=observation.outcome_1r,
        resolved=observation.bars_to_resolution_1r is not None,
        resolved_attr="resolved_1r",
        wins_attr="wins_1r",
        losses_attr="losses_1r",
        flats_attr="flats_1r",
        counters=counters,
    )
    _add_single_outcome_counts(
        outcome=observation.outcome_1_5r,
        resolved=observation.bars_to_resolution_1_5r is not None,
        resolved_attr="resolved_1_5r",
        wins_attr="wins_1_5r",
        losses_attr="losses_1_5r",
        flats_attr="flats_1_5r",
        counters=counters,
    )
    _add_single_outcome_counts(
        outcome=observation.outcome_2r,
        resolved=observation.bars_to_resolution_2r is not None,
        resolved_attr="resolved_2r",
        wins_attr="wins_2r",
        losses_attr="losses_2r",
        flats_attr="flats_2r",
        counters=counters,
    )


def _add_single_outcome_counts(
    *,
    outcome: str,
    resolved: bool,
    resolved_attr: str,
    wins_attr: str,
    losses_attr: str,
    flats_attr: str,
    counters: SetupBCounters,
) -> None:
    if resolved:
        setattr(counters, resolved_attr, getattr(counters, resolved_attr) + 1)
    if outcome == "win":
        setattr(counters, wins_attr, getattr(counters, wins_attr) + 1)
    elif outcome == "loss":
        setattr(counters, losses_attr, getattr(counters, losses_attr) + 1)
    else:
        setattr(counters, flats_attr, getattr(counters, flats_attr) + 1)


def _increment(values: dict[str, int], key: str) -> None:
    values[key] = values.get(key, 0) + 1
