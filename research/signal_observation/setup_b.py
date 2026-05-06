"""Setup B detector for research-layer signal observation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Sequence

from .candles import Candle
from .indicators import atr, pivot_highs, pivot_lows
from .sessions import session_label


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
class TargetOutcome:
    """Outcome for one fixed R target."""

    target_r: Decimal
    target_price: Decimal
    outcome: str
    resolved: bool
    bars_to_resolution: int | None
    mae_r: Decimal | None
    mfe_r: Decimal | None


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
                if invalid_reason in {"pullback_too_deep", "prior_structure_broken"}:
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
                symbol=symbol,
                direction=direction,
                swing=swing,
                prior_opposite=prior_opposite,
                pullback=pullback,
                bos_index=bos_index,
                impulse_size=impulse_size,
            )
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
    symbol: str,
    direction: SignalDirection,
    swing: Pivot,
    prior_opposite: Pivot,
    pullback: Sequence[Candle],
    bos_index: int,
    impulse_size: Decimal,
) -> SetupBObservation | None:
    bos_candle = candles[bos_index]
    atr_at_entry = atr_values[bos_index]
    if atr_at_entry is None:
        return None

    entry = bos_candle.close
    percent_buffer, atr_buffer, chosen_buffer = calculate_stop_buffer(
        entry_price=entry,
        atr_at_entry=atr_at_entry,
    )
    pullback_high = max(candle.high for candle in pullback)
    pullback_low = min(candle.low for candle in pullback)

    if direction is SignalDirection.LONG:
        stop = pullback_low - chosen_buffer
        initial_r = entry - stop
        prior_swing_high = swing.price
        prior_swing_low = prior_opposite.price
        trend_direction = "uptrend"
        pullback_depth = (swing.price - pullback_low) / impulse_size
    else:
        stop = pullback_high + chosen_buffer
        initial_r = stop - entry
        prior_swing_high = prior_opposite.price
        prior_swing_low = swing.price
        trend_direction = "downtrend"
        pullback_depth = (pullback_high - swing.price) / impulse_size

    if initial_r <= Decimal("0"):
        return None

    target_1r = _target_price(entry, initial_r, Decimal("1"), direction)
    target_1_5r = _target_price(entry, initial_r, Decimal("1.5"), direction)
    target_2r = _target_price(entry, initial_r, Decimal("2"), direction)
    outcomes = evaluate_multi_r_outcomes(
        candles,
        entry_index=bos_index,
        entry_price=entry,
        stop=stop,
        initial_r=initial_r,
        direction=direction,
    )
    outcome_1 = outcomes[Decimal("1")]
    outcome_1_5 = outcomes[Decimal("1.5")]
    outcome_2 = outcomes[Decimal("2")]
    signal_time = bos_candle.timestamp.astimezone(UTC)

    return SetupBObservation(
        setup_name=SETUP_NAME,
        symbol=symbol,
        timeframe=TIMEFRAME,
        trend_direction=trend_direction,
        signal_direction=direction,
        signal_time=signal_time,
        signal_hour_utc=signal_time.hour,
        session_label=session_label(signal_time),
        entry_time=signal_time,
        entry_price=entry,
        next_bar_open=candles[bos_index + 1].open if bos_index + 1 < len(candles) else None,
        stop=stop,
        target_1r=target_1r,
        target_1_5r=target_1_5r,
        target_2r=target_2r,
        percent_buffer=percent_buffer,
        atr_buffer=atr_buffer,
        chosen_buffer=chosen_buffer,
        pullback_start_time=pullback[0].timestamp,
        pullback_end_time=pullback[-1].timestamp,
        bos_time=signal_time,
        trend_age_swings=_trend_age_swings(candles, swing),
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


def evaluate_multi_r_outcomes(
    candles: Sequence[Candle],
    *,
    entry_index: int,
    entry_price: Decimal,
    stop: Decimal,
    initial_r: Decimal,
    direction: SignalDirection,
    outcome_window_candles: int = OUTCOME_WINDOW_CANDLES,
) -> dict[Decimal, TargetOutcome]:
    """Evaluate 1R, 1.5R, and 2R outcomes from local candles."""

    window = candles[entry_index + 1 : entry_index + 1 + outcome_window_candles]
    output: dict[Decimal, TargetOutcome] = {}
    for target_r in TARGET_R_VALUES:
        target = _target_price(entry_price, initial_r, target_r, direction)
        output[target_r] = _resolve_target_outcome(
            window=window,
            entry_price=entry_price,
            stop=stop,
            target=target,
            target_r=target_r,
            initial_r=initial_r,
            direction=direction,
        )
    return output


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


def _resolve_target_outcome(
    *,
    window: Sequence[Candle],
    entry_price: Decimal,
    stop: Decimal,
    target: Decimal,
    target_r: Decimal,
    initial_r: Decimal,
    direction: SignalDirection,
) -> TargetOutcome:
    if not window:
        return TargetOutcome(target_r, target, "flat", False, None, None, None)

    if direction is SignalDirection.LONG:
        mfe_r = max((candle.high - entry_price) / initial_r for candle in window)
        mae_r = min((candle.low - entry_price) / initial_r for candle in window)
        for offset, candle in enumerate(window, start=1):
            if candle.low <= stop:
                return TargetOutcome(target_r, target, "loss", True, offset, mae_r, mfe_r)
            if candle.high >= target:
                return TargetOutcome(target_r, target, "win", True, offset, mae_r, mfe_r)
    else:
        mfe_r = max((entry_price - candle.low) / initial_r for candle in window)
        mae_r = min((entry_price - candle.high) / initial_r for candle in window)
        for offset, candle in enumerate(window, start=1):
            if candle.high >= stop:
                return TargetOutcome(target_r, target, "loss", True, offset, mae_r, mfe_r)
            if candle.low <= target:
                return TargetOutcome(target_r, target, "win", True, offset, mae_r, mfe_r)

    return TargetOutcome(target_r, target, "flat", True, len(window), mae_r, mfe_r)


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
    if len(pullback) > MAX_PULLBACK_CANDLES:
        return "pullback_too_long"
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


def _target_price(
    entry: Decimal,
    initial_r: Decimal,
    target_r: Decimal,
    direction: SignalDirection,
) -> Decimal:
    if direction is SignalDirection.LONG:
        return entry + (target_r * initial_r)
    return entry - (target_r * initial_r)


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


def _trend_age_swings(candles: Sequence[Candle], swing: Pivot) -> int:
    return sum(1 for candle in candles[: swing.index + 1] if candle.timestamp <= swing.timestamp)


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
