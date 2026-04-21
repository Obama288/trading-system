from __future__ import annotations

from libs.schemas.common import ExecutionCandidate


def validate_execution_candidate(candidate: ExecutionCandidate) -> None:
    if not candidate.symbol:
        raise ValueError("symbol is required")
    if candidate.entry_price <= 0:
        raise ValueError("entry_price must be positive")
    if candidate.quantity <= 0:
        raise ValueError("quantity must be positive")
    if candidate.stop_loss <= 0:
        raise ValueError("stop_loss must be positive")
    if candidate.order_type not in {"limit", "market"}:
        raise ValueError("unsupported order_type")
