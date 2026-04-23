from __future__ import annotations

from dataclasses import dataclass

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


@dataclass
class _FakePositionRow:
    position_id: str
    execution_id: str
    symbol: str
    status: str
    quantity: float
    entry_price: float


class _FakePositionRepo:
    def __init__(self, *, open_positions: int, pending_admissions: int) -> None:
        self.open_positions = open_positions
        self.pending_admissions = pending_admissions
        self.lock_calls = 0
        self.created_rows: list[_FakePositionRow] = []
        self.by_execution_id: dict[str, _FakePositionRow] = {}

    def acquire_open_position_admission_lock(self) -> None:
        self.lock_calls += 1

    def count_open_positions(self) -> int:
        return self.open_positions

    def count_pending_open_admissions(self, *, mode: str) -> int:
        assert mode == "paper"
        return self.pending_admissions

    def get_by_execution_id(self, execution_id: str):
        return self.by_execution_id.get(execution_id)

    def create_position(
        self,
        *,
        execution_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        opened_at,
        stop_loss: float | None,
        take_profit: list[float],
        ttl_expires_at,
        candidate_id: str | None,
        signal_id: str | None,
    ):
        row = _FakePositionRow(
            position_id=f"pos_{len(self.created_rows) + 1}",
            execution_id=execution_id,
            symbol=symbol,
            status="open",
            quantity=quantity,
            entry_price=entry_price,
        )
        self.created_rows.append(row)
        self.by_execution_id[execution_id] = row
        return row

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

    def write(self, payload: dict) -> None:
        self.events.append(payload)


class _NoopAlert:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def notify(self, payload: dict) -> None:
        self.events.append(payload)


@pytest.mark.asyncio
async def test_place_order_allows_new_admission_below_cap():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    repo = _FakePositionRepo(open_positions=0, pending_admissions=0)
    journal = _NoopJournal()
    alert = _NoopAlert()

    result = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
        position_repo=repo,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert result["accepted"] is True
    assert result["duplicate"] is False
    assert repo.lock_calls == 1
    assert len(repo.created_rows) == 1


@pytest.mark.asyncio
async def test_place_order_rejects_when_open_cap_full():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    repo = _FakePositionRepo(open_positions=1, pending_admissions=0)
    journal = _NoopJournal()
    alert = _NoopAlert()

    result = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
        position_repo=repo,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert result["accepted"] is False
    assert result["error"]["code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["duplicate"] is False
    assert store.get_by_key("idem_001") is None
    assert len(repo.created_rows) == 0


@pytest.mark.asyncio
async def test_place_order_idempotent_retry_unchanged_when_cap_full_after_first():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    repo = _FakePositionRepo(open_positions=0, pending_admissions=0)
    journal = _NoopJournal()
    alert = _NoopAlert()

    first = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_001",
        kill_switch_client=ks,
        store=store,
        position_repo=repo,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )
    repo.open_positions = 99
    repo.pending_admissions = 99
    second = await place_order_use_case(
        candidate_id="cand_001",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_001",
        correlation_id="corr_002",
        kill_switch_client=ks,
        store=store,
        position_repo=repo,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert first["accepted"] is True
    assert second["accepted"] is True
    assert second["duplicate"] is True
    assert second["execution_id"] == first["execution_id"]
    assert len(repo.created_rows) == 1


@pytest.mark.asyncio
async def test_place_order_rejects_when_pending_admission_already_exists():
    store = InMemoryExecutionStore()
    ks = StubKillSwitchClient(trading_enabled=True)
    repo = _FakePositionRepo(open_positions=0, pending_admissions=1)
    journal = _NoopJournal()
    alert = _NoopAlert()

    result = await place_order_use_case(
        candidate_id="cand_002",
        execution_candidate=make_candidate(),
        execution_idempotency_key="idem_002",
        correlation_id="corr_002",
        kill_switch_client=ks,
        store=store,
        position_repo=repo,
        journal_client=journal,
        alert_client=alert,
        execution_mode="paper",
    )

    assert result["accepted"] is False
    assert result["error"]["code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["error"]["current_load"] == 1
