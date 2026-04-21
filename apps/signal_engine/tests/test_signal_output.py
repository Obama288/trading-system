from datetime import datetime, timezone

from apps.signal_engine.application.evaluate_signal import evaluate_signal_use_case
from libs.schemas.common import IndicatorSnapshot, MarketFlags, MarketSnapshot, SignalStatus, TradeDirection


def test_evaluate_signal_returns_no_trade_when_filters_fail():
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
    decision = evaluate_signal_use_case(snapshot)
    assert decision.status == SignalStatus.NO_TRADE
    assert decision.side == TradeDirection.NONE
