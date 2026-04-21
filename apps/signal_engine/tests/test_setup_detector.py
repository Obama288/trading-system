from datetime import datetime, timezone

from apps.signal_engine.domain.setup_detector import detect_breakout_retest
from libs.schemas.common import IndicatorSnapshot, MarketFlags, MarketSnapshot, TradeDirection


def test_detect_breakout_retest_long():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        timestamp=datetime.now(timezone.utc),
        timeframe="15m",
        price=105.0,
        bid=104.9,
        ask=105.1,
        spread_bps=2.0,
        volatility_regime="medium",
        trend_regime="uptrend",
        session="london_ny_overlap",
        indicators=IndicatorSnapshot(ema_20=103.0, ema_50=100.0, rsi_14=62.0, atr_14=2.0),
        market_flags=MarketFlags(news_risk=False, liquidity_ok=True, spread_ok=True),
    )
    found, direction, entry_zone = detect_breakout_retest(snapshot)
    assert found is True
    assert direction == TradeDirection.LONG
    assert entry_zone is not None


def test_detect_breakout_retest_short():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        timestamp=datetime.now(timezone.utc),
        timeframe="15m",
        price=95.0,
        bid=94.9,
        ask=95.1,
        spread_bps=2.0,
        volatility_regime="medium",
        trend_regime="downtrend",
        session="london_ny_overlap",
        indicators=IndicatorSnapshot(ema_20=97.0, ema_50=100.0, rsi_14=40.0, atr_14=2.0),
        market_flags=MarketFlags(news_risk=False, liquidity_ok=True, spread_ok=True),
    )
    found, direction, entry_zone = detect_breakout_retest(snapshot)
    assert found is True
    assert direction == TradeDirection.SHORT
    assert entry_zone is not None
