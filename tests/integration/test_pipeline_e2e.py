from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.execution_service.application.place_order_dry_run import place_order_dry_run_use_case
from apps.execution_service.application.place_order import place_order_use_case
from apps.execution_service.infrastructure.local_clients import DbJournalClient as ExecutionDbJournalClient
from apps.execution_service.infrastructure.local_clients import NoopAlertClient as ExecutionNoopAlertClient
from apps.execution_service.infrastructure.execution_store_db import DbExecutionStore
from apps.orchestrator.application.approve_candidate import approve_candidate_use_case
from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.position_manager.application.open_position import open_position_use_case
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionOpenRequest
from libs.clients.kill_switch_client import StubKillSwitchClient
from libs.db.base import Base
from libs.db.models.execution import ExecutionModel
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.operator_action import OperatorActionModel
from libs.db.models.position import PositionModel
from libs.db.models.trade_candidate import TradeCandidateModel
from libs.db.repositories.operator_action_repo import OperatorActionRepository
from libs.schemas.common import ExecutionCandidate, ExecutionStatus, OrderSide, TradeDirection


def make_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


class DbJournalClient:
    def __init__(self, db: Session) -> None:
        self.db = db

    def write(self, payload: dict) -> None:
        row = JournalEventModel(
            event_id=payload["event_id"],
            event_type=payload["event_type"],
            severity=payload["severity"],
            correlation_id=payload["correlation_id"],
            payload=payload.get("payload", {}),
        )
        self.db.add(row)
        self.db.commit()


class NoopAlertClient:
    def notify(self, payload: dict) -> None:
        return None


class ExecutionServiceClient:
    def __init__(
        self,
        store: DbExecutionStore,
        kill_switch_client: StubKillSwitchClient,
        position_repo: PositionRepository,
        db: Session,
    ) -> None:
        self.store = store
        self.kill_switch_client = kill_switch_client
        self.position_repo = position_repo
        self.journal_client = ExecutionDbJournalClient(db)
        self.alert_client = ExecutionNoopAlertClient()
        self.calls = 0

    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict:
        self.calls += 1
        result = await place_order_use_case(
            candidate_id=candidate_id,
            execution_candidate=ExecutionCandidate(**execution_candidate),
            execution_idempotency_key=f"exec_{candidate_id}",
            correlation_id=correlation_id,
            kill_switch_client=self.kill_switch_client,
            store=self.store,
            position_repo=self.position_repo,
            journal_client=self.journal_client,
            alert_client=self.alert_client,
            execution_mode="paper",
        )
        return {
            "ok": result["accepted"],
            "service": "execution-service",
            "version": "v1",
            "correlation_id": correlation_id,
            "data": result,
            "error": result.get("error"),
        }


class DummyExecutionClient:
    def __init__(self, *, ok: bool, execution_id: str | None = None) -> None:
        self.ok = ok
        self.execution_id = execution_id
        self.calls = 0

    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict:
        self.calls += 1
        data = {} if self.execution_id is None else {"execution_id": self.execution_id}
        return {
            "ok": self.ok,
            "service": "execution-service",
            "version": "v1",
            "correlation_id": correlation_id,
            "data": data,
            "error": None if self.ok else {"code": "EXECUTION_REJECTED"},
        }


def seed_candidate(
    repo: TradeCandidateRepository,
    *,
    candidate_id: str = "cand_001",
    ttl_expires_at: datetime | None = None,
) -> TradeCandidateModel:
    now = datetime.now(timezone.utc)
    row = repo.create_candidate(
        candidate_id=candidate_id,
        signal_id="sig_001",
        risk_id="risk_001",
        review_id="rev_001",
        symbol="BTCUSDT",
        side="long",
        execution_payload_json={
            "symbol": "BTCUSDT",
            "side": OrderSide.BUY.value,
            "order_type": "limit",
            "entry_price": 100.0,
            "quantity": 1.0,
            "stop_loss": 95.0,
            "take_profit": [110.0],
            "time_in_force": "GTC",
        },
        ttl_expires_at=ttl_expires_at or (now + timedelta(minutes=5)),
    )
    if row.ttl_expires_at.tzinfo is None:
        row.ttl_expires_at = row.ttl_expires_at.replace(tzinfo=timezone.utc)
    return row


@pytest.mark.asyncio
async def test_pipeline_happy_path_candidate_submitted_execution_and_position_opened():
    session_factory = make_session_factory()
    with session_factory() as db:
        correlation_id = "corr_e2e_happy"
        candidate_repo = TradeCandidateRepository(db)
        operator_action_repo = OperatorActionRepository(db)
        position_repo = PositionRepository(db)
        journal_client = DbJournalClient(db)
        execution_store = DbExecutionStore(db)
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)
        execution_client = ExecutionServiceClient(execution_store, kill_switch_client, position_repo, db)

        candidate = seed_candidate(candidate_repo)

        approve_result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
            journal_client=journal_client,
            candidate_id=candidate.candidate_id,
            telegram_user_id=123,
            correlation_id=correlation_id,
        )

        assert approve_result["ok"] is True
        assert approve_result["execution_id"] is not None

        refreshed_candidate = candidate_repo.get_candidate(candidate.candidate_id)
        position = position_repo.get_by_execution_id(approve_result["execution_id"])
        execution = db.get(ExecutionModel, approve_result["execution_id"])

        assert refreshed_candidate is not None
        assert refreshed_candidate.status == "submitted"
        assert refreshed_candidate.execution_id is not None
        assert execution is not None
        assert execution.status == "filled"
        assert position is not None


@pytest.mark.asyncio
async def test_pipeline_execution_failure_rolls_back_candidate_and_writes_journal():
    session_factory = make_session_factory()
    with session_factory() as db:
        correlation_id = "corr_e2e_fail"
        candidate_repo = TradeCandidateRepository(db)
        operator_action_repo = OperatorActionRepository(db)
        journal_client = DbJournalClient(db)
        execution_client = DummyExecutionClient(ok=False, execution_id=None)
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)

        candidate = seed_candidate(candidate_repo)

        result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
            journal_client=journal_client,
            candidate_id=candidate.candidate_id,
            telegram_user_id=123,
            correlation_id=correlation_id,
        )

        refreshed_candidate = candidate_repo.get_candidate(candidate.candidate_id)
        failure_event = db.execute(
            select(JournalEventModel).where(JournalEventModel.event_type == "execution_failed_after_approval")
        ).scalar_one_or_none()
        position_count = db.execute(select(PositionModel)).scalars().all()

        assert result["ok"] is False
        assert refreshed_candidate is not None
        assert refreshed_candidate.status == "failed_execution"
        assert refreshed_candidate.execution_id is None
        assert failure_event is not None
        assert failure_event.correlation_id == correlation_id
        assert position_count == []


@pytest.mark.asyncio
async def test_pipeline_kill_switch_active_blocks_approve_without_side_effects():
    session_factory = make_session_factory()
    with session_factory() as db:
        correlation_id = "corr_e2e_kill_switch"
        candidate_repo = TradeCandidateRepository(db)
        operator_action_repo = OperatorActionRepository(db)
        journal_client = DbJournalClient(db)
        execution_client = DummyExecutionClient(ok=True, execution_id="exe_001")
        kill_switch_client = StubKillSwitchClient(trading_enabled=False, incident_code="manual_halt")

        candidate = seed_candidate(candidate_repo)

        result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
            journal_client=journal_client,
            candidate_id=candidate.candidate_id,
            telegram_user_id=123,
            correlation_id=correlation_id,
        )

        refreshed_candidate = candidate_repo.get_candidate(candidate.candidate_id)
        journal_rows = db.execute(select(JournalEventModel)).scalars().all()
        operator_rows = db.execute(select(OperatorActionModel)).scalars().all()

        assert result == {"ok": False, "code": "KILL_SWITCH_ACTIVE"}
        assert refreshed_candidate is not None
        assert refreshed_candidate.status == "pending"
        assert refreshed_candidate.execution_id is None
        assert execution_client.calls == 0
        assert journal_rows == []
        assert operator_rows == []


@pytest.mark.asyncio
async def test_pipeline_expired_candidate_blocks_approve_before_execution():
    session_factory = make_session_factory()
    with session_factory() as db:
        correlation_id = "corr_e2e_expired"
        candidate_repo = TradeCandidateRepository(db)
        operator_action_repo = OperatorActionRepository(db)
        journal_client = DbJournalClient(db)
        execution_client = DummyExecutionClient(ok=True, execution_id="exe_001")
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)

        candidate = seed_candidate(
            candidate_repo,
            ttl_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )

        result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
            journal_client=journal_client,
            candidate_id=candidate.candidate_id,
            telegram_user_id=123,
            correlation_id=correlation_id,
        )

        refreshed_candidate = candidate_repo.get_candidate(candidate.candidate_id)

        assert result == {"ok": False, "code": "EXPIRED"}
        assert refreshed_candidate is not None
        assert refreshed_candidate.status == "expired"
        assert execution_client.calls == 0


@pytest.mark.asyncio
async def test_pipeline_paper_trading_opens_position():
    session_factory = make_session_factory()
    with session_factory() as db:
        correlation_id = "corr_e2e_paper"
        candidate_repo = TradeCandidateRepository(db)
        operator_action_repo = OperatorActionRepository(db)
        position_repo = PositionRepository(db)
        journal_client = DbJournalClient(db)
        execution_store = DbExecutionStore(db)
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)
        execution_client = ExecutionServiceClient(execution_store, kill_switch_client, position_repo, db)

        candidate = seed_candidate(candidate_repo)

        result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
            journal_client=journal_client,
            candidate_id=candidate.candidate_id,
            telegram_user_id=123,
            correlation_id=correlation_id,
        )

        refreshed_candidate = candidate_repo.get_candidate(candidate.candidate_id)
        execution = db.get(ExecutionModel, result["execution_id"])
        position = position_repo.get_by_execution_id(result["execution_id"])
        paper_event = db.execute(
            select(JournalEventModel).where(JournalEventModel.event_type == "paper_execution_filled")
        ).scalar_one_or_none()

        assert result["ok"] is True
        assert refreshed_candidate is not None
        assert refreshed_candidate.status == "submitted"
        assert refreshed_candidate.execution_id == result["execution_id"]
        assert execution is not None
        assert execution.status == "filled"
        assert position is not None
        assert paper_event is not None
        assert execution_client.calls == 1
