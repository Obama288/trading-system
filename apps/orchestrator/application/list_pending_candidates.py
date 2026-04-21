from __future__ import annotations

from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository


def list_pending_candidates_use_case(repo: TradeCandidateRepository) -> list[dict]:
    rows = repo.list_pending()
    return [
        {
            "candidate_id": row.candidate_id,
            "signal_id": row.signal_id,
            "risk_id": row.risk_id,
            "review_id": row.review_id,
            "symbol": row.symbol,
            "side": row.side,
            "status": row.status,
            "ttl_expires_at": row.ttl_expires_at.isoformat(),
        }
        for row in rows
    ]
