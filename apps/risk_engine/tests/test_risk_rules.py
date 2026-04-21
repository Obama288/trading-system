from apps.risk_engine.domain.risk_rules import (
    check_daily_loss_limit,
    check_open_positions_limit,
)
from libs.schemas.common import RiskReasonCode


def test_check_daily_loss_limit_ok():
    ok, code = check_daily_loss_limit(-50.0, 10000.0, 0.02)
    assert ok is True
    assert code == RiskReasonCode.DAILY_LIMIT_OK


def test_check_daily_loss_limit_breached():
    ok, code = check_daily_loss_limit(-250.0, 10000.0, 0.02)
    assert ok is False
    assert code == RiskReasonCode.DAILY_LIMIT_BREACHED


def test_check_open_positions_limit_breached():
    ok, code = check_open_positions_limit(1, 1)
    assert ok is False
    assert code == RiskReasonCode.MAX_OPEN_POSITIONS_REACHED
