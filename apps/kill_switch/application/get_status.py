from __future__ import annotations

from apps.kill_switch.infrastructure.system_state_repo import SystemStateRepository


DEFAULT_KILL_SWITCH_STATE = {
    "trading_enabled": False,
    "kill_switch_active": True,
    "incident_code": "safe_default_not_initialized",
}


def get_kill_switch_status_use_case(repo: SystemStateRepository) -> dict:
    row = repo.get("kill_switch_state")
    if row is None:
        return DEFAULT_KILL_SWITCH_STATE.copy()
    return row.value_json
