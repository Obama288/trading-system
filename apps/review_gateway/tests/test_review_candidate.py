from datetime import datetime, timedelta, timezone

from apps.review_gateway.application.review_candidate import review_candidate_use_case
from libs.schemas.common import (
    IndicatorSnapshot,
    MarketFlags,
    MarketSnapshot,
    RiskDecision,
    RiskReasonCode,
    SignalDecision,
    SignalStatus,
    TradeDirection,
)


def make_signal() -> SignalDecision:
    from libs.schemas.common import EntryZone
    return SignalDecision(
        signal_id="sig_001",
        status=SignalStatus.CANDIDATE,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        setup_type="breakout_retest",
        entry_zone=EntryZone(min=100.0, max=101.0),
        stop_loss=95.0,
        take_profit=[110.0],
        confidence=0.6,
        reasoning_summary="ok",
    )


def make_risk(approved: bool = True) -> RiskDecision:
    return RiskDecision(
        risk_id="risk_001",
        signal_id="sig_001",
        symbol="BTCUSDT",
        approved=approved,
        position_size=1.0 if approved else 0.0,
        notional_usdt=100.0 if approved else 0.0,
        max_loss_usdt=5.0,
        risk_pct_of_equity=0.5,
        leverage=1.0,
        portfolio_exposure_pct=10.0,
        daily_loss_limit_status="ok",
        drawdown_lock=False,
        kill_switch_required=False,
        reason_codes=[RiskReasonCode.RISK_OK] if approved else [RiskReasonCode.RISK_REJECTED],
    )


def make_snapshot(stale: bool = False) -> MarketSnapshot:
    ts = datetime.now(timezone.utc) - timedelta(seconds=60) if stale else datetime.now(timezone.utc)
    return MarketSnapshot(
        symbol="BTCUSDT",
        timestamp=ts,
        timeframe="15m",
        price=100.0,
        bid=99.9,
        ask=100.1,
        spread_bps=2.0,
        volatility_regime="medium",
        trend_regime="uptrend",
        session="london_ny_overlap",
        indicators=IndicatorSnapshot(ema_20=99.0, ema_50=98.0, rsi_14=60.0, atr_14=4.0),
        market_flags=MarketFlags(news_risk=False, liquidity_ok=True, spread_ok=True),
    )


def test_review_candidate_passes():
    decision = review_candidate_use_case(make_signal(), make_risk(True), make_snapshot(False), stale_threshold_seconds=30)
    assert decision.passed is True
    assert decision.execution_candidate is not None


def test_review_candidate_fails_on_stale_snapshot():
    decision = review_candidate_use_case(make_signal(), make_risk(True), make_snapshot(True), stale_threshold_seconds=30)
    assert decision.passed is False
    assert any(flag.value == "MARKET_DATA_STALE" for flag in decision.anomaly_flags)


def test_review_candidate_fails_on_unapproved_risk():
    decision = review_candidate_use_case(make_signal(), make_risk(False), make_snapshot(False), stale_threshold_seconds=30)
    assert decision.passed is False
    assert decision.execution_candidate is None


def test_review_uses_risk_entry_price_not_zone_edge():
    # Risk is the source of truth for entry_price (authority rule #2).
    # candidate_builder must not recompute from signal.entry_zone edges.
    from libs.schemas.common import EntryZone

    signal = make_signal()  # entry_zone min=100.0, max=101.0, side=LONG
    risk = make_risk(True)
    risk.entry_price = 100.5  # midpoint — differs from both zone.min and zone.max

    decision = review_candidate_use_case(signal, risk, make_snapshot(False), stale_threshold_seconds=30)

    assert decision.passed is True
    assert decision.execution_candidate is not None
    assert decision.execution_candidate.entry_price == 100.5
    assert decision.execution_candidate.entry_price != signal.entry_zone.max  # not zone edge
    assert decision.execution_candidate.entry_price != signal.entry_zone.min
