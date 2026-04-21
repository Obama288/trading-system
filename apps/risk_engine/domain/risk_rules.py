from __future__ import annotations

from libs.schemas.common import RiskReasonCode


def check_daily_loss_limit(
    daily_pnl_usdt: float,
    equity_usdt: float,
    max_daily_loss_fraction: float,
) -> tuple[bool, RiskReasonCode]:
    threshold = -equity_usdt * max_daily_loss_fraction
    if daily_pnl_usdt <= threshold:
        return False, RiskReasonCode.DAILY_LIMIT_BREACHED
    return True, RiskReasonCode.DAILY_LIMIT_OK


def check_open_positions_limit(
    open_positions: int,
    max_open_positions: int,
) -> tuple[bool, RiskReasonCode]:
    if open_positions >= max_open_positions:
        return False, RiskReasonCode.MAX_OPEN_POSITIONS_REACHED
    return True, RiskReasonCode.POSITIONS_OK
