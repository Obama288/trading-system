from apps.risk_engine.application.evaluate_risk import evaluate_risk_use_case
from apps.risk_engine.main import AccountState, RiskRequest
from libs.schemas.common import EntryZone, RiskReasonCode, TradeDirection


def test_evaluate_risk_approved():
    req = RiskRequest(
        signal_id="sig_001",
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        entry_zone=EntryZone(min=100.0, max=102.0),
        stop_loss=95.0,
        account_state=AccountState(
            equity_usdt=10000.0,
            daily_pnl_usdt=0.0,
            open_positions=0,
            portfolio_exposure_pct=10.0,
        ),
        correlation_id="corr_001",
    )

    result = evaluate_risk_use_case(req)
    assert result["approved"] is True
    assert RiskReasonCode.RISK_OK in result["reason_codes"]


def test_evaluate_risk_rejected_on_daily_limit():
    req = RiskRequest(
        signal_id="sig_002",
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        entry_zone=EntryZone(min=100.0, max=102.0),
        stop_loss=95.0,
        account_state=AccountState(
            equity_usdt=10000.0,
            daily_pnl_usdt=-250.0,
            open_positions=0,
            portfolio_exposure_pct=10.0,
        ),
        correlation_id="corr_002",
    )

    result = evaluate_risk_use_case(req)
    assert result["approved"] is False
    assert RiskReasonCode.DAILY_LIMIT_BREACHED in result["reason_codes"]


def test_evaluate_risk_rejected_on_zero_equity():
    req = RiskRequest(
        signal_id="sig_003",
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        entry_zone=EntryZone(min=100.0, max=102.0),
        stop_loss=95.0,
        account_state=AccountState(
            equity_usdt=0.0,
            daily_pnl_usdt=0.0,
            open_positions=0,
            portfolio_exposure_pct=0.0,
        ),
        correlation_id="corr_003",
    )

    result = evaluate_risk_use_case(req)
    assert result["approved"] is False
    assert result["kill_switch_required"] is True
    assert RiskReasonCode.KILL_SWITCH_REQUIRED in result["reason_codes"]


def test_evaluate_risk_rejected_on_invalid_stop_distance():
    req = RiskRequest(
        signal_id="sig_004",
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        entry_zone=EntryZone(min=100.0, max=100.0),
        stop_loss=100.0,
        account_state=AccountState(
            equity_usdt=10000.0,
            daily_pnl_usdt=0.0,
            open_positions=0,
            portfolio_exposure_pct=10.0,
        ),
        correlation_id="corr_004",
    )

    result = evaluate_risk_use_case(req)
    assert result["approved"] is False
    assert RiskReasonCode.RISK_REJECTED in result["reason_codes"]


def test_evaluate_risk_rejected_on_max_open_positions():
    req = RiskRequest(
        signal_id="sig_005",
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        entry_zone=EntryZone(min=100.0, max=102.0),
        stop_loss=95.0,
        account_state=AccountState(
            equity_usdt=10000.0,
            daily_pnl_usdt=0.0,
            open_positions=1,
            portfolio_exposure_pct=10.0,
        ),
        correlation_id="corr_005",
    )

    result = evaluate_risk_use_case(req)
    assert result["approved"] is False
    assert RiskReasonCode.MAX_OPEN_POSITIONS_REACHED in result["reason_codes"]
