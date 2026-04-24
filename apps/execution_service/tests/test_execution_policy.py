from __future__ import annotations

import pytest

from apps.execution_service.domain.execution_policy import validate_execution_candidate
from libs.schemas.common import ExecutionCandidate, OrderSide


def _make(
    side: OrderSide = OrderSide.BUY,
    entry_price: float = 100.0,
    stop_loss: float = 95.0,
    take_profit: list[float] | None = None,
) -> ExecutionCandidate:
    return ExecutionCandidate(
        symbol="BTC-USDT",
        side=side,
        order_type="limit",
        entry_price=entry_price,
        quantity=1.0,
        stop_loss=stop_loss,
        take_profit=take_profit or [],
        time_in_force="GTC",
    )


class TestValidateExecutionCandidate:
    def test_long_valid(self):
        validate_execution_candidate(_make(OrderSide.BUY, entry_price=100.0, stop_loss=95.0, take_profit=[110.0]))

    def test_short_valid(self):
        validate_execution_candidate(_make(OrderSide.SELL, entry_price=100.0, stop_loss=105.0, take_profit=[90.0]))

    def test_long_stop_above_entry_rejected(self):
        with pytest.raises(ValueError, match="LONG stop_loss must be below entry_price"):
            validate_execution_candidate(_make(OrderSide.BUY, entry_price=100.0, stop_loss=105.0))

    def test_long_stop_equal_entry_rejected(self):
        with pytest.raises(ValueError, match="LONG stop_loss must be below entry_price"):
            validate_execution_candidate(_make(OrderSide.BUY, entry_price=100.0, stop_loss=100.0))

    def test_short_stop_below_entry_rejected(self):
        with pytest.raises(ValueError, match="SHORT stop_loss must be above entry_price"):
            validate_execution_candidate(_make(OrderSide.SELL, entry_price=100.0, stop_loss=95.0))

    def test_short_stop_equal_entry_rejected(self):
        with pytest.raises(ValueError, match="SHORT stop_loss must be above entry_price"):
            validate_execution_candidate(_make(OrderSide.SELL, entry_price=100.0, stop_loss=100.0))

    def test_long_tp_below_entry_rejected(self):
        with pytest.raises(ValueError, match="LONG take_profit must be above entry_price"):
            validate_execution_candidate(_make(OrderSide.BUY, entry_price=100.0, stop_loss=95.0, take_profit=[90.0]))

    def test_short_tp_above_entry_rejected(self):
        with pytest.raises(ValueError, match="SHORT take_profit must be below entry_price"):
            validate_execution_candidate(_make(OrderSide.SELL, entry_price=100.0, stop_loss=105.0, take_profit=[110.0]))

    def test_no_take_profit_passes_direction_check(self):
        validate_execution_candidate(_make(OrderSide.BUY, entry_price=100.0, stop_loss=95.0, take_profit=[]))
        validate_execution_candidate(_make(OrderSide.SELL, entry_price=100.0, stop_loss=105.0, take_profit=[]))

    def test_rejects_zero_entry_price(self):
        with pytest.raises(ValueError, match="entry_price must be positive"):
            validate_execution_candidate(_make(entry_price=0.0, stop_loss=0.1))

    def test_rejects_zero_quantity(self):
        c = _make()
        c = c.model_copy(update={"quantity": 0.0})
        with pytest.raises(ValueError, match="quantity must be positive"):
            validate_execution_candidate(c)
