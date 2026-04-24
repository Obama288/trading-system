from __future__ import annotations

import pytest

from apps.execution_service.application.place_order import place_order_use_case
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


class _FakeAdmissionRepo:
    def __init__(self, *, open_positions: int, pending_admissions: int) -> None:
        self.open_positions = open_positions
        self.pending_admissions = pending_admissions
        self.lock_calls = 0

    def acquire_open_position_admission_lock(self) -> None:
        self.lock_calls += 1

    def count_open_positions(self) -> int:
        return self.open_positions

    def count_pending_open_admissions(self, *, mode: str) -> int:
        assert mode == "paper"
        return self.pending_admissions


class _FakePositionManagerClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.raises: Exception | None = None

    async def open_position(self, *, payload: dict, correlation_id: str) -> dict:
        if self.raises is not None:
            raise self.raises
        self.calls.append({"payload": payload, "correlation_id": correlation_id})
        return {"ok": True, "data": {"position_id": "pos_1"}, "error": None}

    def record_event(self, *, position_id: str, event_type: str, correlation_id: str, payload: dict):
        return {
            "event_id": "evt_1",
            "position_id": position_id,
            "event_type": event_type,
            "correlation_id": correlation_id,
            "payload": payload,
        }

    @staticmethod
    def to_dict(model: _FakePositionRow) -> dict:
        return {
            "position_id": model.position_id,
            "execution_id": model.execution_id,
            "symbol": model.symbol,
            "status": model.status,
            "quantity": model.quantity,
            "entry_price": model.entry_price,
        }


class _NoopJournal:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def write(self, payload: dict) -> None:
        self.events.append(payload)


class _NoopAlert:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def notify(self, payload: dict) -> None:
        self.events.append(payload)


@pytest.mark.asyncio
async def test_place_order_allows_new_admission_below_cap():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    admission_repo = _FakeAdmissionRepo(open_positions=0, pending_admissions=0)
    pm = _FakePositionManagerClient()
    journal = _NoopJournal()
    alert = _NoopAlert()

    result = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
        admission_repo=admission_repo,
        position_manager_client=pm,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert result["accepted"] is True
    assert result["duplicate"] is False
    assert result["status"] == "position_opened"
    assert admission_repo.lock_calls == 1
    assert len(pm.calls) == 1


@pytest.mark.asyncio
async def test_place_order_rejects_when_open_cap_full():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    admission_repo = _FakeAdmissionRepo(open_positions=1, pending_admissions=0)
    pm = _FakePositionManagerClient()
    journal = _NoopJournal()
    alert = _NoopAlert()

    result = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
        admission_repo=admission_repo,
        position_manager_client=pm,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert result["accepted"] is False
    assert result["error"]["code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["duplicate"] is False
    assert store.get_by_key("idem_001") is None
    assert pm.calls == []


@pytest.mark.asyncio
async def test_place_order_idempotent_retry_unchanged_when_cap_full_after_first():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    admission_repo = _FakeAdmissionRepo(open_positions=0, pending_admissions=0)
    pm = _FakePositionManagerClient()
    journal = _NoopJournal()
    alert = _NoopAlert()

    first = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
        admission_repo=admission_repo,
        position_manager_client=pm,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )
    admission_repo.open_positions = 99
    admission_repo.pending_admissions = 99
    second = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_002",
        kill_switch_client=ks,
        store=store,
        admission_repo=admission_repo,
        position_manager_client=pm,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert first["accepted"] is True
    assert second["accepted"] is True
    assert second["duplicate"] is True
    assert second["execution_id"] == first["execution_id"]
    assert len(pm.calls) == 1


@pytest.mark.asyncio
async def test_place_order_rejects_when_pending_admission_already_exists():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    admission_repo = _FakeAdmissionRepo(open_positions=0, pending_admissions=1)
    pm = _FakePositionManagerClient()
    journal = _NoopJournal()
    alert = _NoopAlert()

    result = await place_order_use_case(
        candidate_id="cand_002",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_002",
        correlation_id="corr_002",
        kill_switch_client=ks,
        store=store,
        admission_repo=admission_repo,
        position_manager_client=pm,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert result["accepted"] is False
    assert result["error"]["code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["error"]["current_load"] == 1
    assert pm.calls == []


@pytest.mark.asyncio
async def test_place_order_marks_execution_failed_when_position_open_throws():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    admission_repo = _FakeAdmissionRepo(open_positions=0, pending_admissions=0)
    pm = _FakePositionManagerClient()
    pm.raises = RuntimeError("position manager down")
    journal = _NoopJournal()
    alert = _NoopAlert()

    result = await place_order_use_case(
        candidate_id="cand_003",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_003",
        correlation_id="corr_003",
        kill_switch_client=ks,
        store=store,
        admission_repo=admission_repo,
        position_manager_client=pm,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert result["accepted"] is False
    assert result["error"]["code"] == "POSITION_OPEN_FAILED"
    stored = store.get_by_execution_id(result["execution_id"])
    assert stored is not None
    assert stored.status == "position_open_failed"
    assert any(evt["event_type"] == "position_open_failed" for evt in journal.events)
