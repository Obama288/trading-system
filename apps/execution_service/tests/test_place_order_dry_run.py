import pytest

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
async def test_place_order_dry_run_blocked_by_kill_switch():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=False, incident_code="manual_halt")

    result = await place_order_dry_run_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
    )

    assert result["accepted"] is False
    assert result["status"] == "blocked"


@pytest.mark.asyncio
async def test_place_order_dry_run_duplicate_request():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)

    first = await place_order_dry_run_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
    )
    second = await place_order_dry_run_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_002",
        kill_switch_client=ks,
        store=store,
    )

    assert first["accepted"] is True
    assert second["accepted"] is True
    assert second["duplicate"] is True
    assert second["execution_id"] == first["execution_id"]


@pytest.mark.asyncio
async def test_place_order_dry_run_accepted():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)

    result = await place_order_dry_run_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
    )

    assert result["accepted"] is True
    assert result["duplicate"] is False
    assert result["mode"] == "paper"
    assert result["status"] == "filled"


@pytest.mark.asyncio
async def test_place_order_dry_run_rejects_empty_idempotency_key():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)

    with pytest.raises(ValueError, match="execution_idempotency_key is required"):
        await place_order_dry_run_use_case(
            candidate_id="cand_001",
            execution_candidate=make_candidate(),
            execution_idempotency_key="",
            correlation_id="corr_001",
            kill_switch_client=ks,
            store=store,
        )
