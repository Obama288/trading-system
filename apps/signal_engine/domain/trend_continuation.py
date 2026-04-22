from __future__ import annotations

from statistics import mean
from uuid import uuid4

from libs.schemas.common import EntryZone, MarketSnapshot, SignalDecision, SignalStatus, TradeDirection


def _compute_ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    multiplier = 2 / (period + 1)
    ema = [values[0]]
    for value in values[1:]:
        ema.append((value - ema[-1]) * multiplier + ema[-1])
    return ema


def _compute_atr(candles: list[dict], period: int = 14) -> list[float]:
    if not candles:
        return []
    trs: list[float] = []
    for index, candle in enumerate(candles):
        prev_close = candles[index - 1]["close"] if index > 0 else candle["close"]
        tr = max(
            candle["high"] - candle["low"],
            abs(candle["high"] - prev_close),
            abs(candle["low"] - prev_close),
        )
        trs.append(tr)
    atr_values: list[float] = []
    for index in range(len(trs)):
        window = trs[max(0, index - period + 1) : index + 1]
        atr_values.append(mean(window))
    return atr_values


def _build_recent_candles(snapshot: MarketSnapshot) -> list[dict]:
    opens = list(snapshot.recent_opens)
    highs = list(snapshot.recent_highs)
    lows = list(snapshot.recent_lows)
    closes = list(snapshot.recent_closes)
    length = min(len(opens), len(highs), len(lows), len(closes))
    if length < 50:
        return []

    return [
        {
            "open": float(opens[index]),
            "high": float(highs[index]),
            "low": float(lows[index]),
            "close": float(closes[index]),
        }
        for index in range(length)
    ]


def _is_market_eligible(snapshot: MarketSnapshot) -> bool:
    flags = snapshot.market_flags
    return not flags.news_risk and flags.liquidity_ok and flags.spread_ok


def _get_higher_timeframe_context(snapshot: MarketSnapshot, candles: list[dict]) -> dict:
    if snapshot.timeframe != "15m" or not _is_market_eligible(snapshot) or len(candles) < 50:
        return {"bias": TradeDirection.NONE, "ema20": None, "ema50": None, "slope": None, "atr": None, "index": None}

    context_candles = candles[:-1]
    if len(context_candles) < 50:
        return {"bias": TradeDirection.NONE, "ema20": None, "ema50": None, "slope": None, "atr": None, "index": None}

    closes = [candle["close"] for candle in context_candles]
    ema20 = _compute_ema(closes, 20)
    ema50 = _compute_ema(closes, 50)
    atr14 = _compute_atr(context_candles, 14)
    index = len(context_candles) - 1
    slope = ema20[index] - ema20[index - 10]

    if ema20[index] > ema50[index] and slope > 0:
        bias = TradeDirection.LONG
    elif ema20[index] < ema50[index] and slope < 0:
        bias = TradeDirection.SHORT
    else:
        bias = TradeDirection.NONE

    return {
        "bias": bias,
        "ema20": ema20[index],
        "ema50": ema50[index],
        "slope": slope,
        "atr": atr14[index],
        "index": index,
    }


def _detect_lower_timeframe_trigger(snapshot: MarketSnapshot, candles: list[dict], context: dict) -> dict:
    bias = context["bias"]
    if bias == TradeDirection.NONE:
        return {
            "direction": TradeDirection.NONE,
            "entry_zone": None,
            "stop_loss": None,
            "take_profit": [],
            "index": None,
        }

    index = context["index"]
    if index is None or index < 1:
        return {
            "direction": TradeDirection.NONE,
            "entry_zone": None,
            "stop_loss": None,
            "take_profit": [],
            "index": None,
        }

    candle = candles[index]
    ema20 = float(context["ema20"])
    atr = float(context["atr"])
    slope = abs(float(context["slope"]))
    slope_threshold = max(atr * 0.1, snapshot.price * 0.0007)
    trigger_distance = abs(candle["close"] - ema20)
    touch_tolerance = atr * 0.35
    entry_zone = EntryZone(min=round(snapshot.price, 6), max=round(snapshot.price, 6))
    prior_window = candles[max(0, index - 4) : index]
    prior_swing_low = min((item["low"] for item in prior_window), default=candle["low"])
    prior_swing_high = max((item["high"] for item in prior_window), default=candle["high"])
    stop_buffer = atr * 0.2

    if bias == TradeDirection.LONG:
        pullback = candle["low"] <= ema20 + touch_tolerance
        trigger = candle["close"] >= ema20 and trigger_distance <= atr * 0.5 and slope >= slope_threshold
        if pullback and trigger:
            stop_anchor = max(candle["low"], prior_swing_low)
            stop_loss = round(stop_anchor - stop_buffer, 6)
            take_profit = [round(snapshot.price + max(snapshot.price - stop_loss, atr) * 2, 6)]
            return {
                "direction": TradeDirection.LONG,
                "entry_zone": entry_zone,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "index": index,
                "stop_anchor": stop_anchor,
            }

    if bias == TradeDirection.SHORT:
        pullback = candle["high"] >= ema20 - touch_tolerance
        trigger = candle["close"] <= ema20 and trigger_distance <= atr * 0.5 and slope >= slope_threshold
        if pullback and trigger:
            stop_anchor = min(candle["high"], prior_swing_high)
            stop_loss = round(stop_anchor + stop_buffer, 6)
            take_profit = [round(snapshot.price - max(stop_loss - snapshot.price, atr) * 2, 6)]
            return {
                "direction": TradeDirection.SHORT,
                "entry_zone": entry_zone,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "index": index,
                "stop_anchor": stop_anchor,
            }

    return {
        "direction": TradeDirection.NONE,
        "entry_zone": None,
        "stop_loss": None,
        "take_profit": [],
        "index": index,
    }


def _score_candidate(snapshot: MarketSnapshot, direction: TradeDirection, candles: list[dict], index: int, context: dict) -> tuple[float, str]:
    confidence = 0.45
    bonuses: list[str] = []
    candle = candles[index]
    prev_candle = candles[index - 1] if index > 0 else candle
    ema20 = float(context["ema20"])
    atr = float(context["atr"])
    slope = abs(float(context["slope"]))
    distance_to_ema = abs(candle["close"] - ema20)

    confirm_long = direction == TradeDirection.LONG and candle["close"] >= prev_candle["close"] and candle["close"] > candle["open"]
    confirm_short = direction == TradeDirection.SHORT and candle["close"] <= prev_candle["close"] and candle["close"] < candle["open"]
    if confirm_long or confirm_short:
        confidence += 0.10
        bonuses.append("impulse_close")

    if snapshot.session == "london_ny_overlap":
        confidence += 0.08
        bonuses.append("london_ny_overlap")

    if slope >= atr * 0.5:
        confidence += 0.07
        bonuses.append("strong_slope")

    if distance_to_ema <= atr * 0.12:
        confidence += 0.05
        bonuses.append("clean_touch")

    confidence = min(confidence, 0.85)
    reasoning_summary = "trend_continuation trigger with htf_like_context"
    if bonuses:
        reasoning_summary += f"; bonuses={', '.join(bonuses)}"
    else:
        reasoning_summary += "; bonuses=none"
    return confidence, reasoning_summary


def detect_trend_continuation(snapshot: MarketSnapshot) -> SignalDecision | None:
    candles = _build_recent_candles(snapshot)
    if not candles:
        return None

    context = _get_higher_timeframe_context(snapshot, candles)
    trigger = _detect_lower_timeframe_trigger(snapshot, candles, context)
    direction = trigger["direction"]
    if direction == TradeDirection.NONE:
        return None

    index = trigger["index"]
    if index is None:
        return None

    confidence, reasoning_summary = _score_candidate(snapshot, direction, candles, index, context)

    return SignalDecision(
        signal_id=f"sig_{uuid4().hex}",
        status=SignalStatus.CANDIDATE,
        symbol=snapshot.symbol,
        side=direction,
        setup_type="trend_continuation",
        entry_zone=trigger["entry_zone"],
        stop_loss=trigger["stop_loss"],
        take_profit=trigger["take_profit"],
        confidence=confidence,
        invalidation="Python candidate only; reasoning layer not wired yet.",
        reasoning_summary=reasoning_summary,
    )
