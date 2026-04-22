import pytest

from apps.execution_service.application.place_order_dry_run import place_order_dry_run_use_case
from apps.execution_service.infrastructure.execution_store import InMemoryExecutionStore
from apps.execution_service.infrastructure.kill_switch_client import StubKillSwitchClient
from libs.schemas.common import ExecutionCandidate, OrderSide


@pytest.mark.asyncio
async def test_kill_switch_active_blocks_execution():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=False, incident_code="manual_halt")

    candidate = ExecutionCandidate(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="limit",
        entry_price=100.0,
        quantity=1.0,
        stop_loss=95.0,
        take_profit=[110.0],
        time_in_force="GTC",
    )

    result = await place_order_dry_run_use_case(
        candidate_id="cand_001",
        execution_candidate=candidate,
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
    )

    assert result["accepted"] is False
    assert result["status"] == "blocked"
    assert result["error"]["code"] == "KILL_SWITCH_ACTIVE"
