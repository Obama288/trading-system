from __future__ import annotations

from apps.kill_switch.infrastructure.system_state_repo import SystemStateRepository


def resume_use_case(repo: SystemStateRepository, *, actor: str) -> dict:
    # This direct resume path is acceptable for paper-trading validation only.
    # It is not sufficient for live-safe resume logic, which still needs stronger
    # operator checks and reconciliation-aware recovery before live trading.
    state = {
        "trading_enabled": True,
        "kill_switch_active": False,
        "incident_code": "paper_mode_resumed",
    }
    repo.upsert_in_session("kill_switch_state", state, updated_by=actor)
    repo.upsert_in_session("trading_enabled", {"value": True}, updated_by=actor)
    # caller owns the commit so state + operator_action + journal are one transaction
    return state
