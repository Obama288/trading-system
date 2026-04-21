from __future__ import annotations

from uuid import uuid4

from apps.signal_engine.application.detect_setup import detect_setup_use_case
from apps.signal_engine.application.run_filters import run_filters_use_case
from libs.schemas.common import MarketSnapshot, SignalDecision, SignalStatus, TradeDirection


def evaluate_signal_use_case(snapshot: MarketSnapshot) -> SignalDecision:
    passed, filter_reasons = run_filters_use_case(snapshot)
    if not passed:
        return SignalDecision(
            signal_id=f"sig_{uuid4().hex}",
            status=SignalStatus.NO_TRADE,
            symbol=snapshot.symbol,
            side=TradeDirection.NONE,
            setup_type="none",
            confidence=0.0,
            reasoning_summary="; ".join(r.value for r in filter_reasons),
        )

    found, direction, entry_zone = detect_setup_use_case(snapshot)
    if not found or direction == TradeDirection.NONE:
        return SignalDecision(
            signal_id=f"sig_{uuid4().hex}",
            status=SignalStatus.NO_TRADE,
            symbol=snapshot.symbol,
            side=TradeDirection.NONE,
            setup_type="breakout_retest",
            confidence=0.0,
            reasoning_summary="No valid setup detected by Python rules.",
        )

    atr = snapshot.indicators.atr_14
    stop_loss = None
    take_profit: list[float] = []

    if direction == TradeDirection.LONG:
        stop_loss = round(snapshot.price - atr, 6)
        take_profit = [round(snapshot.price + atr * 2, 6)]
    elif direction == TradeDirection.SHORT:
        stop_loss = round(snapshot.price + atr, 6)
        take_profit = [round(snapshot.price - atr * 2, 6)]

    return SignalDecision(
        signal_id=f"sig_{uuid4().hex}",
        status=SignalStatus.CANDIDATE,
        symbol=snapshot.symbol,
        side=direction,
        setup_type="breakout_retest",
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=0.6,  # stub confidence — replace with Sonnet output when reasoning layer is wired
        invalidation="Python candidate only; reasoning layer not wired yet.",
        reasoning_summary="Candidate detected by deterministic setup rules.",
    )
