from __future__ import annotations

from datetime import datetime, timezone

from libs.schemas.common import IndicatorSnapshot, MarketFlags, MarketSnapshot


def _ema(closes: list[float], period: int) -> float:
    alpha = 2 / (period + 1)
    value = sum(closes[:period]) / period
    for price in closes[period:]:
        value = alpha * price + (1 - alpha) * value
    return value


def build_market_snapshot(
    symbol: str,
    timeframe: str,
    last_price: float,
    bid: float,
    ask: float,
    closes: list[float],
    highs: list[float],
    lows: list[float],
    opens: list[float] | None = None,
    news_risk: bool = False,
    session: str = "unknown",
) -> MarketSnapshot:
    if len(closes) < 50 or len(highs) < 50 or len(lows) < 50:
        raise ValueError("Insufficient candle data: need at least 50 candles")
    if opens is None:
        opens = [closes[0], *closes[:-1]]
    if len(opens) < 50:
        raise ValueError("Insufficient candle data: need at least 50 candles")

    spread_bps = round((ask - bid) / last_price * 10000, 4) if last_price > 0 else 0.0
    liquidity_ok = spread_bps < 50.0
    spread_ok = spread_bps < 20.0

    ema_20 = _ema(closes, 20)
    ema_50 = _ema(closes, 50)

    gains = [max(closes[i] - closes[i - 1], 0) for i in range(-14, 0)]
    losses = [max(closes[i - 1] - closes[i], 0) for i in range(-14, 0)]
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    rsi_14 = 100.0 - (100.0 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100.0

    tr_list = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(-14, 0)
    ]
    atr_14 = sum(tr_list) / 14

    volatility_regime = "high" if atr_14 / last_price > 0.02 else "medium" if atr_14 / last_price > 0.005 else "low"
    trend_regime = "uptrend" if ema_20 > ema_50 else "downtrend"

    return MarketSnapshot(
        symbol=symbol,
        timestamp=datetime.now(timezone.utc),
        timeframe=timeframe,
        price=last_price,
        bid=bid,
        ask=ask,
        spread_bps=spread_bps,
        volatility_regime=volatility_regime,
        trend_regime=trend_regime,
        session=session,
        indicators=IndicatorSnapshot(ema_20=ema_20, ema_50=ema_50, rsi_14=rsi_14, atr_14=atr_14),
        market_flags=MarketFlags(news_risk=news_risk, liquidity_ok=liquidity_ok, spread_ok=spread_ok),
        recent_opens=list(opens),
        recent_highs=list(highs),
        recent_lows=list(lows),
        recent_closes=list(closes),
    )
