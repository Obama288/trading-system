from datetime import datetime, timedelta, timezone

from apps.position_manager.domain.position import Position
from apps.position_manager.domain.rules import (
    check_stop_loss,
    check_take_profit,
    check_ttl_expiry,
    evaluate_exit_rules,
)
from libs.schemas.common import PositionStatus, TradeDirection


def make_position(side: TradeDirection, *, stop_loss: float | None = 95.0, take_profit: list[float] | None = None):
    now = datetime.now(timezone.utc)
    return Position(
        position_id="pos_001",
        execution_id="exe_001",
        symbol="BTCUSDT",
        side=side,
        status=PositionStatus.OPEN,
        quantity=1.0,
        entry_price=100.0,
        stop_loss=stop_loss,
        take_profit=take_profit or [110.0],
        opened_at=now,
        ttl_expires_at=now + timedelta(minutes=5),
    )


def test_long_stop_loss_triggers_close():
    position = make_position(TradeDirection.LONG, stop_loss=95.0)
    result = check_stop_loss(position, 94.5)
    assert result.should_close is True
    assert result.reason.value == "stop_loss"


def test_short_take_profit_triggers_close():
    position = make_position(TradeDirection.SHORT, take_profit=[90.0], stop_loss=105.0)
    result = check_take_profit(position, 89.0)
    assert result.should_close is True
    assert result.reason.value == "take_profit"


def test_ttl_expiry_triggers_close():
    position = make_position(TradeDirection.LONG)
    result = check_ttl_expiry(position, position.ttl_expires_at + timedelta(seconds=1))
    assert result.should_close is True
    assert result.reason.value == "expired"


def test_rule_evaluation_prefers_stop_loss_before_other_rules():
    now = datetime.now(timezone.utc)
    position = Position(
        position_id="pos_001",
        execution_id="exe_001",
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        status=PositionStatus.OPEN,
        quantity=1.0,
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=[110.0],
        opened_at=now - timedelta(minutes=10),
        ttl_expires_at=now - timedelta(seconds=1),
    )
    result = evaluate_exit_rules(position, 94.0, now)
    assert result.should_close is True
    assert result.reason.value == "stop_loss"
