import pytest

from apps.execution_service.application.place_order_dry_run import place_order_dry_run_use_case
from apps.execution_service.infrastructure.execution_store import InMemoryExecutionStore
from apps.execution_service.infrastructure.kill_switch_client import StubKillSwitchClient
from libs.clients.kill_switch_client import (
    KillSwitchAuthError,
    KillSwitchTimeoutError,
    KillSwitchUnavailableError,
    KillSwitchError,
)
from libs.schemas.common import ExecutionCandidate, OrderSide


class _ErrorKillSwitchClient:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def get_status(self, correlation_id: str) -> dict:
        raise self._exc


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


@pytest.mark.asyncio
@pytest.mark.parametrize("exc,expected_code", [
    (KillSwitchAuthError("auth failed"), "AUTH_FAILURE"),
    (KillSwitchTimeoutError("timed out"), "KILL_SWITCH_TIMEOUT"),
    (KillSwitchUnavailableError("unreachable"), "KILL_SWITCH_UNAVAILABLE"),
    (KillSwitchError("generic error"), "KILL_SWITCH_ERROR"),
])
async def test_kill_switch_error_taxonomy(exc, expected_code):
    store = InMemoryExecutionStore()
    ks = _ErrorKillSwitchClient(exc)

    result = await place_order_dry_run_use_case(
        candidate_id="cand_ks_err",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_ks_err",
        correlation_id="corr_ks_err",
        kill_switch_client=ks,
        store=store,
    )

    assert result["accepted"] is False
    assert result["status"] == "blocked"
    assert result["error"]["code"] == expected_code
