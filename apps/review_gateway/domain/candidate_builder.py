from __future__ import annotations

from libs.schemas.common import ExecutionCandidate, RiskDecision, SignalDecision, trade_direction_to_order_side


def build_execution_candidate(signal: SignalDecision, risk: RiskDecision) -> ExecutionCandidate:
    if signal.entry_zone is None or signal.stop_loss is None:
        raise ValueError("Signal is incomplete for execution candidate build")
    if risk.position_size <= 0:
        raise ValueError("Risk position size must be positive")

    entry_price = signal.entry_zone.max if signal.side.value == "long" else signal.entry_zone.min

    return ExecutionCandidate(
        symbol=signal.symbol,
        side=trade_direction_to_order_side(signal.side),
        order_type="limit",
        entry_price=entry_price,
        quantity=risk.position_size,
        stop_loss=signal.stop_loss,
        take_profit=signal.take_profit,
        time_in_force="GTC",
    )
