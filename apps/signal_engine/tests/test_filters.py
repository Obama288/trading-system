from datetime import datetime, timezone

from apps.signal_engine.domain.filters import basic_market_filters
from libs.schemas.common import FilterReason, IndicatorSnapshot, MarketFlags, MarketSnapshot


def test_basic_market_filters_pass():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        timestamp=datetime.now(timezone.utc),
        timeframe="15m",
        price=100.0,
        bid=99.9,
        ask=100.1,
        spread_bps=2.0,
        volatility_regime="medium",
        trend_regime="uptrend",
        session="london_ny_overlap",
        indicators=IndicatorSnapshot(ema_20=99.0, ema_50=98.0, rsi_14=60.0, atr_14=1.5),
        market_flags=MarketFlags(news_risk=False, liquidity_ok=True, spread_ok=True),
    )
    passed, reasons = basic_market_filters(snapshot)
    assert passed is True
    assert reasons == []


def test_basic_market_filters_fail_on_news_risk():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        timestamp=datetime.now(timezone.utc),
        timeframe="15m",
        price=100.0,
        bid=99.9,
        ask=100.1,
        spread_bps=2.0,
        volatility_regime="medium",
        trend_regime="uptrend",
        session="london_ny_overlap",
        indicators=IndicatorSnapshot(ema_20=99.0, ema_50=98.0, rsi_14=60.0, atr_14=1.5),
        market_flags=MarketFlags(news_risk=True, liquidity_ok=True, spread_ok=True),
    )
    passed, reasons = basic_market_filters(snapshot)
    assert passed is False
    assert FilterReason.NEWS_RISK in reasons
