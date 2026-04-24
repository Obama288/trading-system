from __future__ import annotations

from apps.kill_switch.infrastructure.system_state_repo import SystemStateRepository


def halt_use_case(repo: SystemStateRepository, reason: str, actor: str) -> dict:
    state = {
        "trading_enabled": False,
        "kill_switch_active": True,
        "incident_code": reason,
    }
    repo.upsert_in_session("kill_switch_state", state, updated_by=actor)
    repo.upsert_in_session("trading_enabled", {"value": False}, updated_by=actor)
    # caller owns the commit so state + operator_action + journal are one transaction
    return state
