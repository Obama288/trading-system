from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from statistics import mean

from research.hypothesis_agent.analysis.market_regime import compute_atr, compute_ema
from research.simcore.candles import Candle as _SimCandle
from research.simcore.models import (
    Direction as _SimDirection,
    FillPolicy as _FillPolicy,
    InvalidTrade as _SimInvalidTrade,
    TradeSpec as _TradeSpec,
)
from research.simcore.simulator import simulate_trade as _simulate_trade_fn


PATTERN_NAMES = (
    "breakout_retest",
    "trend_continuation",
)

_ZERO = Decimal("0")
_TWO = Decimal("2")


def _dict_to_candle(d: dict) -> _SimCandle:
    return _SimCandle(
        timestamp=d["timestamp"],
        open=Decimal(str(d["open"])),
        high=Decimal(str(d["high"])),
        low=Decimal(str(d["low"])),
        close=Decimal(str(d["close"])),
        volume=Decimal(str(d["volume"])),
    )


def _bar_duration(candles: list[dict]) -> timedelta:
    if len(candles) < 2:
        return timedelta(hours=1)
    return candles[1]["timestamp"] - candles[0]["timestamp"]


def _append_simcore_trade(
    trades: list[dict],
    candles: list[dict],
    signal_index: int,
    *,
    direction: str,
    stop: float,
    target_r: Decimal = _TWO,
    max_bars: int | None = None,
) -> None:
    """Append a trade resolved via simcore (NEXT_BAR_OPEN from signal_index).

    signal_index is the bar whose close completes the pattern.
    Entry is at the open of candles[signal_index + 1] (NEXT_BAR_OPEN).
    target_r defaults to 2R (all hypothesis patterns target 2R).
    """
    stop_d = Decimal(str(stop))
    if stop_d <= _ZERO:
        return

    remaining = len(candles) - signal_index - 1
    outcome_window = remaining if max_bars is None else min(remaining, max_bars)
    if outcome_window <= 0:
        return

    sim_candles = [_dict_to_candle(c) for c in candles]
    duration = _bar_duration(candles)

    spec = _TradeSpec(
        symbol="hypothesis",
        direction=_SimDirection(direction.lower()),
        signal_index=signal_index,
        stop_price=stop_d,
        target_r_values=(target_r,),
        outcome_window_bars=outcome_window,
        fill=_FillPolicy.NEXT_BAR_OPEN,
    )
    sim_result = _simulate_trade_fn(sim_candles, spec, duration)
    if isinstance(sim_result, _SimInvalidTrade):
        return

    t = sim_result.targets[target_r]
    trades.append({
        "direction": direction,
        "session": candles[signal_index]["session"],
        "win": t.outcome == "win",
        "rr": float(t.final_r_gross),
        "duration_candles": t.bars_to_resolution,
    })


def analyze_breakout_retest(candles: list[dict]) -> list[dict]:
    trades: list[dict] = []
    atr_values = compute_atr(candles, 14)
    for index in range(12, len(candles) - 2):
        prior = candles[index - 12 : index]
        resistance = max(candle["high"] for candle in prior)
        support = min(candle["low"] for candle in prior)
        breakout = candles[index]
        retest = candles[index + 1]
        atr = atr_values[index]

        if breakout["close"] > resistance and retest["low"] <= resistance <= retest["close"]:
            stop = resistance - max(atr, 1e-6)
            _append_simcore_trade(trades, candles, index + 1, direction="LONG", stop=stop)

        if breakout["close"] < support and retest["high"] >= support >= retest["close"]:
            stop = support + max(atr, 1e-6)
            _append_simcore_trade(trades, candles, index + 1, direction="SHORT", stop=stop)
    return trades


def analyze_consolidation_breakout(candles: list[dict]) -> list[dict]:
    trades: list[dict] = []
    atr_values = compute_atr(candles, 14)
    for index in range(10, len(candles) - 1):
        box = candles[index - 8 : index]
        box_high = max(candle["high"] for candle in box)
        box_low = min(candle["low"] for candle in box)
        box_range = box_high - box_low
        avg_body = mean(candle["body"] for candle in box)
        atr = atr_values[index]
        candle = candles[index]

        if box_range < atr * 1.5 and candle["close"] > box_high and candle["body"] > avg_body * 1.2:
            stop = box_low
            _append_simcore_trade(trades, candles, index, direction="LONG", stop=stop)

        if box_range < atr * 1.5 and candle["close"] < box_low and candle["body"] > avg_body * 1.2:
            stop = box_high
            _append_simcore_trade(trades, candles, index, direction="SHORT", stop=stop)
    return trades


def analyze_trend_continuation(candles: list[dict]) -> list[dict]:
    trades: list[dict] = []
    closes = [candle["close"] for candle in candles]
    ema20 = compute_ema(closes, 20)
    atr_values = compute_atr(candles, 14)
    for index in range(21, len(candles) - 1):
        atr = atr_values[index]
        ema = ema20[index]
        prev_ema = ema20[index - 3]
        slope = ema - prev_ema
        candle = candles[index]

        if slope > 0 and candle["low"] <= ema <= candle["close"]:
            stop = min(candle["low"], ema) - atr * 0.5
            _append_simcore_trade(trades, candles, index, direction="LONG", stop=stop)

        if slope < 0 and candle["high"] >= ema >= candle["close"]:
            stop = max(candle["high"], ema) + atr * 0.5
            _append_simcore_trade(trades, candles, index, direction="SHORT", stop=stop)
    return trades


def analyze_momentum(candles: list[dict]) -> list[dict]:
    trades: list[dict] = []
    atr_values = compute_atr(candles, 14)
    for index in range(5, len(candles) - 1):
        seq = candles[index - 3 : index]
        atr = atr_values[index]
        if all(candle["close"] > candle["open"] and candle["body"] > atr * 0.3 for candle in seq):
            pullback = candles[index]
            if pullback["close"] < seq[-1]["close"]:
                stop = min(pullback["low"], seq[-1]["low"]) - atr * 0.5
                _append_simcore_trade(trades, candles, index, direction="LONG", stop=stop)

        if all(candle["close"] < candle["open"] and candle["body"] > atr * 0.3 for candle in seq):
            pullback = candles[index]
            if pullback["close"] > seq[-1]["close"]:
                stop = max(pullback["high"], seq[-1]["high"]) + atr * 0.5
                _append_simcore_trade(trades, candles, index, direction="SHORT", stop=stop)
    return trades


def analyze_patterns(candles: list[dict]) -> dict[str, list[dict]]:
    return {
        "breakout_retest": analyze_breakout_retest(candles),
        "trend_continuation": analyze_trend_continuation(candles),
    }
