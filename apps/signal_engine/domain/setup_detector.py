from __future__ import annotations

from libs.schemas.common import EntryZone, MarketSnapshot, TradeDirection


def detect_breakout_retest(snapshot: MarketSnapshot) -> tuple[bool, TradeDirection, EntryZone | None]:
    ema_20 = snapshot.indicators.ema_20
    ema_50 = snapshot.indicators.ema_50
    rsi = snapshot.indicators.rsi_14
    price = snapshot.price
    atr = snapshot.indicators.atr_14

    if price > ema_20 > ema_50 and rsi > 55:
        entry_zone = EntryZone(min=round(price - atr * 0.1, 6), max=round(price + atr * 0.1, 6))
        return True, TradeDirection.LONG, entry_zone

    if price < ema_20 < ema_50 and rsi < 45:
        entry_zone = EntryZone(min=round(price - atr * 0.1, 6), max=round(price + atr * 0.1, 6))
        return True, TradeDirection.SHORT, entry_zone

    return False, TradeDirection.NONE, None
