from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apps.position_manager.domain.position import Position
from libs.schemas.common import PositionCloseReason, TradeDirection


@dataclass(slots=True)
class RuleTrigger:
    should_close: bool
    reason: PositionCloseReason | None = None
    message: str | None = None


def check_stop_loss(position: Position, market_price: float | None) -> RuleTrigger:
    if market_price is None or position.stop_loss is None:
        return RuleTrigger(should_close=False)

    if position.side == TradeDirection.LONG and market_price <= position.stop_loss:
        return RuleTrigger(True, PositionCloseReason.STOP_LOSS, "long stop-loss breached")
    if position.side == TradeDirection.SHORT and market_price >= position.stop_loss:
        return RuleTrigger(True, PositionCloseReason.STOP_LOSS, "short stop-loss breached")
    return RuleTrigger(should_close=False)


def check_take_profit(position: Position, market_price: float | None) -> RuleTrigger:
    if market_price is None or not position.take_profit:
        return RuleTrigger(should_close=False)

    target = position.take_profit[0]
    if position.side == TradeDirection.LONG and market_price >= target:
        return RuleTrigger(True, PositionCloseReason.TAKE_PROFIT, "long take-profit reached")
    if position.side == TradeDirection.SHORT and market_price <= target:
        return RuleTrigger(True, PositionCloseReason.TAKE_PROFIT, "short take-profit reached")
    return RuleTrigger(should_close=False)


def check_ttl_expiry(position: Position, now: datetime) -> RuleTrigger:
    if position.ttl_expires_at is None:
        return RuleTrigger(should_close=False)
    if now >= position.ttl_expires_at:
        return RuleTrigger(True, PositionCloseReason.EXPIRED, "position TTL expired")
    return RuleTrigger(should_close=False)


def evaluate_exit_rules(position: Position, market_price: float | None, now: datetime) -> RuleTrigger:
    for rule in (
        check_stop_loss(position, market_price),
        check_take_profit(position, market_price),
        check_ttl_expiry(position, now),
    ):
        if rule.should_close:
            return rule
    return RuleTrigger(should_close=False)
