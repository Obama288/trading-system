from __future__ import annotations

from typing import Protocol

from apps.risk_engine.domain.risk_rules import (
    check_daily_loss_limit,
    check_open_positions_limit,
)
from apps.risk_engine.domain.sizing import (
    compute_max_loss_usdt,
    compute_notional_usdt,
    compute_position_size,
    compute_risk_pct_of_equity,
)
from libs.config.settings import load_all_configs
from libs.schemas.common import RiskReasonCode


class RiskRequestLike(Protocol):
    signal_id: str
    symbol: str
    entry_zone: object
    stop_loss: float
    account_state: object


def evaluate_risk_use_case(req: RiskRequestLike) -> dict:
    # confidence is intentionally ignored here — see authority rules.
    # admissibility is based solely on deterministic inputs.
    # NOTE: account_state is still caller-supplied in this MVP pass.
    # Before live use, migrate to a trusted state source (position manager / DB / exchange reconciliation).
    # drawdown_lock remains hardcoded False in this MVP pass because it requires persisted historical equity/drawdown state.
    configs = load_all_configs()
    risk_cfg = configs["risk"]["risk"]

    equity = req.account_state.equity_usdt
    if equity <= 0:
        return {
            "approved": False,
            "entry_price": 0.0,
            "position_size": 0.0,
            "notional_usdt": 0.0,
            "max_loss_usdt": 0.0,
            "risk_pct_of_equity": 0.0,
            "leverage": 0.0,
            "portfolio_exposure_pct": req.account_state.portfolio_exposure_pct,
            "daily_loss_limit_status": "breached",
            "drawdown_lock": False,  # requires historical drawdown state; not available in MVP
            "kill_switch_required": True,
            "reason_codes": [RiskReasonCode.RISK_REJECTED, RiskReasonCode.KILL_SWITCH_REQUIRED],
        }

    daily_ok, daily_code = check_daily_loss_limit(
        daily_pnl_usdt=req.account_state.daily_pnl_usdt,
        equity_usdt=equity,
        max_daily_loss_fraction=float(risk_cfg["max_daily_loss_pct"]) / 100.0,
    )

    positions_ok, positions_code = check_open_positions_limit(
        open_positions=req.account_state.open_positions,
        max_open_positions=int(risk_cfg["max_open_positions"]),
    )

    if req.entry_zone.max <= 0 or req.stop_loss <= 0:
        return {
            "approved": False,
            "entry_price": 0.0,
            "position_size": 0.0,
            "notional_usdt": 0.0,
            "max_loss_usdt": 0.0,
            "risk_pct_of_equity": 0.0,
            "leverage": 0.0,
            "portfolio_exposure_pct": req.account_state.portfolio_exposure_pct,
            "daily_loss_limit_status": "ok" if daily_ok else "breached",
            "drawdown_lock": False,
            "kill_switch_required": False,
            "reason_codes": [RiskReasonCode.RISK_REJECTED],
        }

    # MVP assumption: use midpoint(entry_zone) as synthetic entry price until execution-ready pricing is available.
    entry_price = (req.entry_zone.min + req.entry_zone.max) / 2
    max_loss_usdt = compute_max_loss_usdt(
        equity_usdt=equity,
        max_risk_fraction=float(risk_cfg["max_risk_per_trade_pct"]) / 100.0,
    )

    try:
        position_size = compute_position_size(
            entry_price=entry_price,
            stop_loss=req.stop_loss,
            max_loss_usdt=max_loss_usdt,
        )
    except ValueError:
        return {
            "approved": False,
            "entry_price": 0.0,
            "position_size": 0.0,
            "notional_usdt": 0.0,
            "max_loss_usdt": max_loss_usdt,
            "risk_pct_of_equity": compute_risk_pct_of_equity(max_loss_usdt, equity),
            "leverage": 0.0,
            "portfolio_exposure_pct": req.account_state.portfolio_exposure_pct,
            "daily_loss_limit_status": "ok" if daily_ok else "breached",
            "drawdown_lock": False,
            "kill_switch_required": False,
            "reason_codes": [RiskReasonCode.RISK_REJECTED],
        }

    notional = compute_notional_usdt(entry_price=entry_price, position_size=position_size)
    risk_pct = compute_risk_pct_of_equity(max_loss_usdt=max_loss_usdt, equity_usdt=equity)

    approved = daily_ok and positions_ok
    reason_codes: list[RiskReasonCode] = [RiskReasonCode.RISK_OK] if approved else [RiskReasonCode.RISK_REJECTED]
    reason_codes.append(daily_code)
    reason_codes.append(positions_code)

    return {
        "approved": approved,
        "entry_price": entry_price if approved else 0.0,
        "position_size": position_size if approved else 0.0,
        "notional_usdt": notional if approved else 0.0,
        "max_loss_usdt": max_loss_usdt,
        "risk_pct_of_equity": risk_pct,
        "leverage": float(risk_cfg["max_leverage"]) if approved else 0.0,
        "portfolio_exposure_pct": req.account_state.portfolio_exposure_pct,
        "daily_loss_limit_status": "ok" if daily_ok else "breached",
        "drawdown_lock": False,
        "kill_switch_required": False,
        "reason_codes": reason_codes,
    }
