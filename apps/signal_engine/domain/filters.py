from __future__ import annotations

from libs.schemas.common import FilterReason, MarketSnapshot


def basic_market_filters(snapshot: MarketSnapshot) -> tuple[bool, list[FilterReason]]:
    reasons: list[FilterReason] = []

    if snapshot.price <= 0:
        reasons.append(FilterReason.PRICE_INVALID)
    if snapshot.bid <= 0 or snapshot.ask <= 0:
        reasons.append(FilterReason.ORDERBOOK_TOP_INVALID)
    if not snapshot.market_flags.liquidity_ok:
        reasons.append(FilterReason.LIQUIDITY_NOT_OK)
    if not snapshot.market_flags.spread_ok:
        reasons.append(FilterReason.SPREAD_NOT_OK)
    if snapshot.market_flags.news_risk:
        reasons.append(FilterReason.NEWS_RISK)
    if snapshot.indicators.atr_14 <= 0:
        reasons.append(FilterReason.ATR_INVALID)

    # stale snapshot authority belongs to market_data.
    # signal_engine should respect upstream freshness metadata if/when it is included in the request envelope.
    return len(reasons) == 0, reasons
