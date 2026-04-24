from __future__ import annotations

from libs.schemas.common import ExecutionCandidate, OrderSide


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

    if candidate.side == OrderSide.BUY:
        if candidate.stop_loss >= candidate.entry_price:
            raise ValueError(
                f"LONG stop_loss must be below entry_price "
                f"(stop_loss={candidate.stop_loss}, entry_price={candidate.entry_price})"
            )
        for tp in candidate.take_profit:
            if tp <= candidate.entry_price:
                raise ValueError(
                    f"LONG take_profit must be above entry_price "
                    f"(take_profit={tp}, entry_price={candidate.entry_price})"
                )
    elif candidate.side == OrderSide.SELL:
        if candidate.stop_loss <= candidate.entry_price:
            raise ValueError(
                f"SHORT stop_loss must be above entry_price "
                f"(stop_loss={candidate.stop_loss}, entry_price={candidate.entry_price})"
            )
        for tp in candidate.take_profit:
            if tp >= candidate.entry_price:
                raise ValueError(
                    f"SHORT take_profit must be below entry_price "
                    f"(take_profit={tp}, entry_price={candidate.entry_price})"
                )
