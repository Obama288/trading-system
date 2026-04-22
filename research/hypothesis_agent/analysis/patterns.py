from __future__ import annotations

from statistics import mean

from research.hypothesis_agent.analysis.market_regime import compute_atr, compute_ema


PATTERN_NAMES = (
    "breakout_retest",
    "trend_continuation",
)


def _simulate_trade(
    candles: list[dict],
    signal_index: int,
    *,
    direction: str,
    entry: float,
    stop: float,
    target: float,
    max_bars: int | None = None,
) -> dict | None:
    if stop <= 0 or entry <= 0:
        return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None

    end_index = len(candles) - 1 if max_bars is None else min(len(candles) - 1, signal_index + max_bars)
    for index in range(signal_index + 1, end_index + 1):
        candle = candles[index]
        if direction == "LONG":
            if candle["low"] <= stop:
                return {"win": False, "rr": -1.0, "duration_candles": index - signal_index}
            if candle["high"] >= target:
                return {"win": True, "rr": round((target - entry) / risk, 2), "duration_candles": index - signal_index}
        else:
            if candle["high"] >= stop:
                return {"win": False, "rr": -1.0, "duration_candles": index - signal_index}
            if candle["low"] <= target:
                return {"win": True, "rr": round((entry - target) / risk, 2), "duration_candles": index - signal_index}

    last_close = candles[end_index]["close"]
    if direction == "LONG":
        rr = round((last_close - entry) / risk, 2)
        return {"win": rr > 0, "rr": rr, "duration_candles": end_index - signal_index}
    rr = round((entry - last_close) / risk, 2)
    return {"win": rr > 0, "rr": rr, "duration_candles": end_index - signal_index}


def _append_trade(
    trades: list[dict],
    candles: list[dict],
    signal_index: int,
    *,
    direction: str,
    entry: float,
    stop: float,
    target: float,
) -> None:
    outcome = _simulate_trade(
        candles,
        signal_index,
        direction=direction,
        entry=entry,
        stop=stop,
        target=target,
    )
    if outcome is None:
        return
    trades.append(
        {
            "direction": direction,
            "session": candles[signal_index]["session"],
            **outcome,
        }
    )


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
            entry = resistance
            stop = entry - max(atr, 1e-6)
            target = entry + (entry - stop) * 2
            _append_trade(trades, candles, index + 1, direction="LONG", entry=entry, stop=stop, target=target)

        if breakout["close"] < support and retest["high"] >= support >= retest["close"]:
            entry = support
            stop = entry + max(atr, 1e-6)
            target = entry - (stop - entry) * 2
            _append_trade(trades, candles, index + 1, direction="SHORT", entry=entry, stop=stop, target=target)
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
            entry = candle["close"]
            stop = box_low
            target = entry + max(entry - stop, atr) * 2
            _append_trade(trades, candles, index, direction="LONG", entry=entry, stop=stop, target=target)

        if box_range < atr * 1.5 and candle["close"] < box_low and candle["body"] > avg_body * 1.2:
            entry = candle["close"]
            stop = box_high
            target = entry - max(stop - entry, atr) * 2
            _append_trade(trades, candles, index, direction="SHORT", entry=entry, stop=stop, target=target)
    return trades


def analyze_trend_continuation(candles: list[dict]) -> list[dict]:
    trades: list[dict] = []
    closes = [candle["close"] for candle in candles]
    ema20 = compute_ema(closes, 20)
    atr_values = compute_atr(candles, 14)
    for index in range(21, len(candles) - 1):
        price = candles[index]["close"]
        atr = atr_values[index]
        ema = ema20[index]
        prev_ema = ema20[index - 3]
        slope = ema - prev_ema
        candle = candles[index]

        if slope > 0 and candle["low"] <= ema <= candle["close"]:
            entry = price
            stop = min(candle["low"], ema) - atr * 0.5
            target = entry + max(entry - stop, atr) * 2
            _append_trade(trades, candles, index, direction="LONG", entry=entry, stop=stop, target=target)

        if slope < 0 and candle["high"] >= ema >= candle["close"]:
            entry = price
            stop = max(candle["high"], ema) + atr * 0.5
            target = entry - max(stop - entry, atr) * 2
            _append_trade(trades, candles, index, direction="SHORT", entry=entry, stop=stop, target=target)
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
                entry = seq[-1]["close"]
                stop = min(pullback["low"], seq[-1]["low"]) - atr * 0.5
                target = entry + max(entry - stop, atr) * 2
                _append_trade(trades, candles, index, direction="LONG", entry=entry, stop=stop, target=target)

        if all(candle["close"] < candle["open"] and candle["body"] > atr * 0.3 for candle in seq):
            pullback = candles[index]
            if pullback["close"] > seq[-1]["close"]:
                entry = seq[-1]["close"]
                stop = max(pullback["high"], seq[-1]["high"]) + atr * 0.5
                target = entry - max(stop - entry, atr) * 2
                _append_trade(trades, candles, index, direction="SHORT", entry=entry, stop=stop, target=target)
    return trades


def analyze_patterns(candles: list[dict]) -> dict[str, list[dict]]:
    return {
        "breakout_retest": analyze_breakout_retest(candles),
        "trend_continuation": analyze_trend_continuation(candles),
    }
