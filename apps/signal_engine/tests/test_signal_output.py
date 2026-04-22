from datetime import datetime, timezone

from apps.signal_engine.application.evaluate_signal import evaluate_signal_use_case
from apps.signal_engine.domain.trend_continuation import (
    _get_higher_timeframe_context,
    _build_recent_candles,
    _detect_lower_timeframe_trigger,
    detect_trend_continuation,
)
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


def _make_trend_continuation_snapshot() -> MarketSnapshot:
    recent_opens: list[float] = []
    recent_closes: list[float] = []
    recent_highs: list[float] = []
    recent_lows: list[float] = []
    price = 100.0
    for index in range(60):
        open_price = price
        step = 0.05 if index < 40 else 0.005
        close_price = open_price + step
        high_price = close_price + 0.12
        low_price = open_price - 0.12
        recent_opens.append(round(open_price, 6))
        recent_closes.append(round(close_price, 6))
        recent_highs.append(round(high_price, 6))
        recent_lows.append(round(low_price, 6))
        price = close_price

    recent_opens[-1] = round(recent_closes[-2] - 0.01, 6)
    recent_closes[-1] = round(recent_closes[-2] + 0.015, 6)
    recent_highs[-1] = round(recent_closes[-1] + 0.12, 6)
    recent_lows[-1] = round(recent_closes[-1] - 0.10, 6)

    return MarketSnapshot(
        symbol="BTCUSDT",
        timestamp=datetime.now(timezone.utc),
        timeframe="15m",
        price=recent_closes[-1],
        bid=recent_closes[-1] - 0.1,
        ask=recent_closes[-1] + 0.1,
        spread_bps=2.0,
        volatility_regime="medium",
        trend_regime="uptrend",
        session="london_ny_overlap",
        indicators=IndicatorSnapshot(ema_20=recent_closes[-20], ema_50=recent_closes[-50], rsi_14=50.0, atr_14=1.2),
        market_flags=MarketFlags(news_risk=False, liquidity_ok=True, spread_ok=True),
        recent_opens=recent_opens,
        recent_highs=recent_highs,
        recent_lows=recent_lows,
        recent_closes=recent_closes,
    )


def _make_short_trend_continuation_snapshot() -> MarketSnapshot:
    recent_opens: list[float] = []
    recent_closes: list[float] = []
    recent_highs: list[float] = []
    recent_lows: list[float] = []
    price = 110.0
    for index in range(60):
        open_price = price
        step = -0.05 if index < 40 else -0.005
        close_price = open_price + step
        high_price = open_price + 0.12
        low_price = close_price - 0.12
        recent_opens.append(round(open_price, 6))
        recent_closes.append(round(close_price, 6))
        recent_highs.append(round(high_price, 6))
        recent_lows.append(round(low_price, 6))
        price = close_price

    recent_opens[-1] = round(recent_closes[-2] + 0.01, 6)
    recent_closes[-1] = round(recent_closes[-2] - 0.015, 6)
    recent_highs[-1] = round(recent_closes[-1] + 0.10, 6)
    recent_lows[-1] = round(recent_closes[-1] - 0.12, 6)

    return MarketSnapshot(
        symbol="BTCUSDT",
        timestamp=datetime.now(timezone.utc),
        timeframe="15m",
        price=recent_closes[-1],
        bid=recent_closes[-1] - 0.1,
        ask=recent_closes[-1] + 0.1,
        spread_bps=2.0,
        volatility_regime="medium",
        trend_regime="downtrend",
        session="asia",
        indicators=IndicatorSnapshot(ema_20=recent_closes[-20], ema_50=recent_closes[-50], rsi_14=45.0, atr_14=1.2),
        market_flags=MarketFlags(news_risk=False, liquidity_ok=True, spread_ok=True),
        recent_opens=recent_opens,
        recent_highs=recent_highs,
        recent_lows=recent_lows,
        recent_closes=recent_closes,
    )


def test_higher_timeframe_context_returns_long_bias():
    snapshot = _make_trend_continuation_snapshot()

    context = _get_higher_timeframe_context(snapshot, _build_recent_candles(snapshot))

    assert context["bias"] == TradeDirection.LONG


def test_higher_timeframe_context_excludes_current_trigger_candle_influence():
    snapshot = _make_trend_continuation_snapshot()
    snapshot.recent_closes[-1] = snapshot.recent_closes[-1] + 5.0
    snapshot.recent_highs[-1] = snapshot.recent_closes[-1] + 0.12
    snapshot.price = snapshot.recent_closes[-1]
    snapshot.ask = snapshot.price + 0.1
    snapshot.bid = snapshot.price - 0.1

    context = _get_higher_timeframe_context(snapshot, _build_recent_candles(snapshot))

    assert context["bias"] == TradeDirection.LONG
    assert context["ema20"] < snapshot.price


def test_higher_timeframe_context_returns_short_bias():
    snapshot = _make_short_trend_continuation_snapshot()

    context = _get_higher_timeframe_context(snapshot, _build_recent_candles(snapshot))

    assert context["bias"] == TradeDirection.SHORT


def test_higher_timeframe_context_returns_none_when_timeframe_not_15m():
    snapshot = _make_trend_continuation_snapshot()
    snapshot.timeframe = "5m"

    context = _get_higher_timeframe_context(snapshot, _build_recent_candles(snapshot))

    assert context["bias"] == TradeDirection.NONE


def test_detect_trend_continuation_long_candidate():
    snapshot = _make_trend_continuation_snapshot()

    decision = detect_trend_continuation(snapshot)

    assert decision is not None
    assert decision.status == SignalStatus.CANDIDATE
    assert decision.side == TradeDirection.LONG
    assert decision.setup_type == "trend_continuation"
    assert decision.stop_loss is not None
    assert decision.take_profit
    assert 0.45 <= decision.confidence <= 0.85
    assert decision.stop_loss < snapshot.price
    assert decision.take_profit[0] > snapshot.price


def test_trend_continuation_stop_is_tighter_than_previous_wide_anchor():
    snapshot = _make_trend_continuation_snapshot()
    candles = _build_recent_candles(snapshot)
    context = _get_higher_timeframe_context(snapshot, candles)
    decision = detect_trend_continuation(snapshot)

    assert decision is not None
    wide_stop = round(min(candles[-1]["low"], float(context["ema20"])) - float(context["atr"]) * 0.5, 6)
    assert decision.stop_loss > wide_stop


def test_prior_swing_anchor_can_differ_from_current_candle_extreme():
    snapshot = _make_trend_continuation_snapshot()
    snapshot.recent_lows[-2] = snapshot.recent_lows[-1] + 0.03
    snapshot.recent_lows[-3] = snapshot.recent_lows[-1] + 0.02
    candles = _build_recent_candles(snapshot)
    context = _get_higher_timeframe_context(snapshot, candles)
    trigger = _detect_lower_timeframe_trigger(snapshot, candles, context)

    assert trigger["direction"] == TradeDirection.LONG
    assert trigger["stop_anchor"] > candles[-1]["low"]


def test_detect_trend_continuation_requires_context_alignment():
    snapshot = _make_trend_continuation_snapshot()
    snapshot.timeframe = "5m"

    decision = detect_trend_continuation(snapshot)

    assert decision is None


def test_confidence_bonuses_do_not_block_candidate_creation():
    snapshot = _make_short_trend_continuation_snapshot()

    decision = detect_trend_continuation(snapshot)

    assert decision is not None
    assert decision.status == SignalStatus.CANDIDATE
    assert decision.side == TradeDirection.SHORT
    assert 0.45 <= decision.confidence <= 0.85
    assert decision.stop_loss > snapshot.price
    assert decision.take_profit[0] < snapshot.price
    assert "impulse_close" in decision.reasoning_summary


def test_evaluate_signal_falls_back_to_native_trend_continuation():
    snapshot = _make_trend_continuation_snapshot()

    decision = evaluate_signal_use_case(snapshot)

    assert decision.status == SignalStatus.CANDIDATE
    assert decision.side == TradeDirection.LONG
    assert decision.setup_type == "trend_continuation"


def test_detect_trend_continuation_returns_none_when_market_not_eligible():
    snapshot = _make_trend_continuation_snapshot()
    snapshot.market_flags = MarketFlags(news_risk=True, liquidity_ok=True, spread_ok=True)

    decision = detect_trend_continuation(snapshot)

    assert decision is None
