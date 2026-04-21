from __future__ import annotations

from datetime import datetime, timezone

from libs.schemas.common import AnomalyFlag, MarketSnapshot, RiskDecision, SignalDecision


def snapshot_age_seconds(snapshot: MarketSnapshot) -> int:
    return int((datetime.now(timezone.utc) - snapshot.timestamp).total_seconds())


def detect_anomalies(
    signal: SignalDecision,
    risk: RiskDecision,
    snapshot: MarketSnapshot,
    stale_threshold_seconds: int,
) -> list[AnomalyFlag]:
    flags: list[AnomalyFlag] = []

    if snapshot_age_seconds(snapshot) > stale_threshold_seconds:
        flags.append(AnomalyFlag.MARKET_DATA_STALE)

    if signal.symbol != risk.symbol or signal.signal_id != risk.signal_id:
        flags.append(AnomalyFlag.SIGNAL_RISK_MISMATCH)

    atr = snapshot.indicators.atr_14
    if atr > 0 and signal.stop_loss is not None:
        distance = abs(snapshot.price - signal.stop_loss)
        if distance < atr * 0.25:
            flags.append(AnomalyFlag.STOP_TOO_TIGHT_FOR_ATR)

    return flags
