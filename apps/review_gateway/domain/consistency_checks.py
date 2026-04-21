from __future__ import annotations

from enum import Enum

from libs.schemas.common import RiskDecision, SignalDecision


class ReviewConsistencyReason(str, Enum):
    SYMBOL_MISMATCH = "SYMBOL_MISMATCH"
    SIGNAL_ID_MISMATCH = "SIGNAL_ID_MISMATCH"
    RISK_NOT_APPROVED = "RISK_NOT_APPROVED"
    SIGNAL_NOT_CANDIDATE = "SIGNAL_NOT_CANDIDATE"
    SIGNAL_DIRECTION_INVALID = "SIGNAL_DIRECTION_INVALID"
    ENTRY_ZONE_MISSING = "ENTRY_ZONE_MISSING"
    STOP_LOSS_MISSING = "STOP_LOSS_MISSING"


def check_signal_risk_consistency(
    signal: SignalDecision,
    risk: RiskDecision,
) -> tuple[bool, list[ReviewConsistencyReason]]:
    reasons: list[ReviewConsistencyReason] = []

    if signal.symbol != risk.symbol:
        reasons.append(ReviewConsistencyReason.SYMBOL_MISMATCH)
    if signal.signal_id != risk.signal_id:
        reasons.append(ReviewConsistencyReason.SIGNAL_ID_MISMATCH)
    if not risk.approved:
        reasons.append(ReviewConsistencyReason.RISK_NOT_APPROVED)
    if signal.status.value != "candidate":
        reasons.append(ReviewConsistencyReason.SIGNAL_NOT_CANDIDATE)
    if signal.side.value == "none":
        reasons.append(ReviewConsistencyReason.SIGNAL_DIRECTION_INVALID)
    if signal.entry_zone is None:
        reasons.append(ReviewConsistencyReason.ENTRY_ZONE_MISSING)
    if signal.stop_loss is None:
        reasons.append(ReviewConsistencyReason.STOP_LOSS_MISSING)

    return len(reasons) == 0, reasons
