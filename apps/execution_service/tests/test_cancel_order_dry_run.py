import pytest

from apps.execution_service.application.cancel_order_dry_run import cancel_order_dry_run_use_case
from apps.execution_service.application.place_order_dry_run import place_order_dry_run_use_case
from apps.execution_service.infrastructure.execution_store import InMemoryExecutionStore
from apps.execution_service.infrastructure.kill_switch_client import StubKillSwitchClient
from libs.schemas.common import ExecutionCandidate, OrderSide


def make_candidate() -> ExecutionCandidate:
    return ExecutionCandidate(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="limit",
        entry_price=100.0,
        quantity=1.0,
        stop_loss=95.0,
        take_profit=[110.0],
        time_in_force="GTC",
    )


@pytest.mark.asyncio
async def test_cancel_order_dry_run_ok():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)

    placed = await place_order_dry_run_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
    )

    result = cancel_order_dry_run_use_case(
        execution_id=placed["execution_id"],
        store=store,
    )

    assert result["ok"] is True
    assert result["status"] == "cancelled"


def test_cancel_order_dry_run_not_found():
    store = InMemoryExecutionStore()

    result = cancel_order_dry_run_use_case(
        execution_id="exe_missing",
        store=store,
    )

    assert result["ok"] is False
    assert result["status"] == "not_found"
