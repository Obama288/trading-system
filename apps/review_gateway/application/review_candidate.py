from __future__ import annotations

from uuid import uuid4

from apps.review_gateway.domain.anomaly_rules import detect_anomalies
from apps.review_gateway.domain.candidate_builder import build_execution_candidate
from apps.review_gateway.domain.consistency_checks import check_signal_risk_consistency
from libs.schemas.common import AnomalyFlag, MarketSnapshot, ReviewDecision, RiskDecision, SignalDecision


def review_candidate_use_case(
    signal: SignalDecision,
    risk: RiskDecision,
    snapshot: MarketSnapshot,
    stale_threshold_seconds: int = 30,
) -> ReviewDecision:
    consistent, reasons = check_signal_risk_consistency(signal, risk)
    anomaly_flags = detect_anomalies(signal, risk, snapshot, stale_threshold_seconds=stale_threshold_seconds)

    if not consistent:
        if AnomalyFlag.SIGNAL_RISK_MISMATCH not in anomaly_flags:
            anomaly_flags.append(AnomalyFlag.SIGNAL_RISK_MISMATCH)
        return ReviewDecision(
            review_id=f"rev_{uuid4().hex}",
            signal_id=signal.signal_id,
            risk_id=risk.risk_id,
            passed=False,
            anomaly_flags=anomaly_flags,
            review_notes="; ".join(reason.value for reason in reasons),
            execution_candidate=None,
        )

    try:
        execution_candidate = build_execution_candidate(signal, risk)
    except ValueError as exc:
        if AnomalyFlag.EXECUTION_CANDIDATE_INCOMPLETE not in anomaly_flags:
            anomaly_flags.append(AnomalyFlag.EXECUTION_CANDIDATE_INCOMPLETE)
        return ReviewDecision(
            review_id=f"rev_{uuid4().hex}",
            signal_id=signal.signal_id,
            risk_id=risk.risk_id,
            passed=False,
            anomaly_flags=anomaly_flags,
            review_notes=str(exc),
            execution_candidate=None,
        )

    passed = len(anomaly_flags) == 0
    return ReviewDecision(
        review_id=f"rev_{uuid4().hex}",
        signal_id=signal.signal_id,
        risk_id=risk.risk_id,
        passed=passed,
        anomaly_flags=anomaly_flags,
        review_notes="Candidate is execution-ready." if passed else "Candidate contains anomalies.",
        execution_candidate=execution_candidate if passed else None,
    )
