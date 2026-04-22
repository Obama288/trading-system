from __future__ import annotations

from statistics import mean


def compute_ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    multiplier = 2 / (period + 1)
    ema = [values[0]]
    for value in values[1:]:
        ema.append((value - ema[-1]) * multiplier + ema[-1])
    return ema


def compute_atr(candles: list[dict], period: int = 14) -> list[float]:
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


def detect_market_regime(candles: list[dict], *, slope_threshold: float) -> str:
    if len(candles) < 30:
        return "quiet"

    closes = [candle["close"] for candle in candles]
    ema20 = compute_ema(closes, 20)
    atr_values = compute_atr(candles, 14)
    current_atr = atr_values[-1]
    avg_atr20 = mean(atr_values[-20:])
    avg_body20 = mean(candle["body"] for candle in candles[-20:])
    current_price = closes[-1]
    baseline = abs(ema20[-5]) if abs(ema20[-5]) > 1e-9 else 1.0
    slope = (ema20[-1] - ema20[-5]) / 5 / baseline

    if avg_atr20 > 0 and current_atr > avg_atr20 * 2:
        return "volatile"
    if avg_atr20 > 0 and current_atr < avg_atr20 * 0.5 and avg_body20 < current_atr * 0.3:
        return "quiet"
    if abs(slope) > slope_threshold and ((slope > 0 and current_price > ema20[-1]) or (slope < 0 and current_price < ema20[-1])):
        return "trending"
    return "ranging"
