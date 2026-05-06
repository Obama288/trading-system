"""Setup A detector for research-layer signal observation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Sequence

from .candles import Candle
from .indicators import atr
from .models import BtcScore, Direction, ObservationStatus, SetupId, SignalObservation
from .sessions import session_label


CONTEXT_TIMEFRAME = "4H"
TRIGGER_TIMEFRAME = "1H"
LOOKBACK_CANDLES_4H = 48
MIN_TOUCHES = 3
VOLUME_LOOKBACK = 20
RETEST_WINDOW_1H = 24
OUTCOME_WINDOW_CANDLES = 24


def detect_setup_a(
    context_candles_4h: Sequence[Candle],
    trigger_candles_1h: Sequence[Candle],
    *,
    symbol: str,
    source_exchange: str,
    direction: Direction = Direction.LONG,
    btc_score: BtcScore = BtcScore.CHOP,
) -> list[SignalObservation]:
    """Detect complete SQ_1.0 Setup A long observations from local candles."""

    if direction is not Direction.LONG:
        raise NotImplementedError("Setup A short detection is not implemented yet")
    if not symbol:
        raise ValueError("symbol must not be empty")
    if not source_exchange:
        raise ValueError("source_exchange must not be empty")
    if not context_candles_4h:
        return []
    if not trigger_candles_1h:
        return []

    context_atr = atr(context_candles_4h, period=14)
    trigger_atr = atr(trigger_candles_1h, period=14)
    observations: list[SignalObservation] = []

    for index, breakout_candle in enumerate(context_candles_4h):
        atr_4h = context_atr[index]
        if atr_4h is None:
            continue
        if index < LOOKBACK_CANDLES_4H:
            continue

        base = context_candles_4h[index - LOOKBACK_CANDLES_4H : index]
        if not base:
            continue
        range_high = max(candle.high for candle in base)
        range_low = min(candle.low for candle in base)
        if range_high - range_low < atr_4h:
            continue

        touch_tolerance = atr_4h * Decimal("0.15")
        touches = [
            candle
            for candle in base
            if range_high - touch_tolerance <= candle.high <= range_high
        ]
        if len(touches) < MIN_TOUCHES:
            continue

        if breakout_candle.close <= range_high:
            continue
        if breakout_candle.close - range_high < atr_4h * Decimal("0.2"):
            continue
        candle_range = breakout_candle.high - breakout_candle.low
        if candle_range <= Decimal("0"):
            continue
        candle_body = abs(breakout_candle.close - breakout_candle.open)
        if candle_body < candle_range * Decimal("0.5"):
            continue

        average_volume = (
            sum(candle.volume for candle in context_candles_4h[index - VOLUME_LOOKBACK : index])
            / Decimal(VOLUME_LOOKBACK)
        )
        if breakout_candle.volume <= average_volume * Decimal("1.5"):
            continue

        observation = _detect_retest_observation(
            trigger_candles_1h=trigger_candles_1h,
            trigger_atr=trigger_atr,
            breakout_time=breakout_candle.timestamp,
            range_high=range_high,
            symbol=symbol,
            source_exchange=source_exchange,
            btc_score=btc_score,
        )
        if observation is not None:
            observations.append(observation)

    return observations


def _detect_retest_observation(
    *,
    trigger_candles_1h: Sequence[Candle],
    trigger_atr: Sequence[Decimal | None],
    breakout_time: datetime,
    range_high: Decimal,
    symbol: str,
    source_exchange: str,
    btc_score: BtcScore,
) -> SignalObservation | None:
    after_breakout = [
        (index, candle)
        for index, candle in enumerate(trigger_candles_1h)
        if candle.timestamp > breakout_time
    ][:RETEST_WINDOW_1H]

    retest_candidates: list[tuple[int, Candle]] = []
    for index, candle in after_breakout:
        atr_1h = trigger_atr[index]
        if atr_1h is None:
            continue
        retest_tolerance = atr_1h * Decimal("0.25")
        if candle.low <= range_high + retest_tolerance and candle.high >= range_high - retest_tolerance:
            retest_candidates.append((index, candle))
        if retest_candidates and candle.close > range_high:
            entry_index = index + 1
            if entry_index >= len(trigger_candles_1h):
                return None
            entry_candle = trigger_candles_1h[entry_index]
            stop_atr = trigger_atr[index]
            if stop_atr is None:
                return None
            retest_swing_low = min(item.low for _, item in retest_candidates)
            stop = retest_swing_low - (stop_atr * Decimal("0.1"))
            entry = entry_candle.open
            initial_r = entry - stop
            if initial_r <= Decimal("0"):
                return None
            target = entry + (Decimal("2") * initial_r)
            signal_time = candle.timestamp.astimezone(UTC)

            return SignalObservation(
                observation_id=_observation_id(symbol, signal_time),
                created_at_utc=signal_time,
                source_exchange=source_exchange,
                symbol=symbol,
                setup_id=SetupId.A,
                direction=Direction.LONG,
                context_timeframe=CONTEXT_TIMEFRAME,
                trigger_timeframe=TRIGGER_TIMEFRAME,
                signal_time=signal_time,
                entry_time_theoretical=entry_candle.timestamp,
                entry_price_theoretical=entry,
                stop_price_theoretical=stop,
                target_price_theoretical=target,
                initial_r=initial_r,
                btc_score=btc_score,
                session_utc_hour=signal_time.hour,
                session_label=session_label(signal_time),
                status=ObservationStatus.VALID,
                outcome_window_candles=OUTCOME_WINDOW_CANDLES,
            )

    return None


def _observation_id(symbol: str, signal_time: datetime) -> str:
    compact_time = signal_time.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"setup-a-{symbol.lower()}-{compact_time}"
