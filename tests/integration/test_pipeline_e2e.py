from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.execution_service.application.place_order import place_order_use_case
from apps.execution_service.infrastructure.local_clients import DbJournalClient as ExecutionDbJournalClient
from apps.execution_service.infrastructure.local_clients import NoopAlertClient as ExecutionNoopAlertClient
from apps.execution_service.infrastructure.position_admission_repo import DbPositionAdmissionRepo
from apps.execution_service.infrastructure.execution_store_db import DbExecutionStore
from apps.orchestrator.application.approve_candidate import approve_candidate_use_case
from apps.orchestrator.application.evaluate_pipeline import evaluate_pipeline_use_case
from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from apps.position_manager.application.close_position import close_position_use_case
from apps.position_manager.application.open_position import open_position_use_case
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionCloseRequest, PositionOpenRequest
from libs.clients.kill_switch_client import StubKillSwitchClient
from libs.db.base import Base
from libs.db.models.execution import ExecutionModel
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.operator_action import OperatorActionModel
from libs.db.models.position import PositionModel
from libs.db.models.position_event import PositionEventModel
from libs.db.models.trade_candidate import TradeCandidateModel
from libs.db.repositories.operator_action_repo import OperatorActionRepository
from ops.paper_pipeline_runner import PaperHarnessAccountState, run_cycle
from libs.schemas.common import (
    EntryZone,
    ExecutionCandidate,
    OrderSide,
    PositionCloseReason,
    ReviewDecision,
    RiskDecision,
    RiskReasonCode,
    SignalDecision,
    SignalStatus,
    TradeDirection,
)


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

    async def write(self, payload: dict) -> None:
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
    async def notify(self, payload: dict) -> None:
        return None


class ExecutionServiceClient:
    def __init__(
        self,
        store: DbExecutionStore,
        kill_switch_client: StubKillSwitchClient,
        admission_repo: DbPositionAdmissionRepo,
        position_manager_client,
        db: Session,
    ) -> None:
        self.store = store
        self.kill_switch_client = kill_switch_client
        self.admission_repo = admission_repo
        self.position_manager_client = position_manager_client
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
            admission_repo=self.admission_repo,
            position_manager_client=self.position_manager_client,
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


class InProcPositionManagerClient:
    def __init__(self, *, repo: PositionRepository, journal_client: DbJournalClient, alert_client: NoopAlertClient) -> None:
        self.repo = repo
        self.journal_client = journal_client
        self.alert_client = alert_client

    async def open_position(self, *, payload: dict, correlation_id: str) -> dict:
        _ = correlation_id
        req = PositionOpenRequest(**payload)
        result = await open_position_use_case(
            repo=self.repo,
            journal_client=self.journal_client,
            alert_client=self.alert_client,
            req=req,
        )
        return {"ok": True, "data": result, "error": None}


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
    # TradeCandidateRepository.create_candidate no longer commits; tests that seed directly
    # must persist explicitly to reflect real request behavior.
    repo.db.commit()
    repo.db.refresh(row)
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
        admission_repo = DbPositionAdmissionRepo(db)
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)
        position_manager_client = InProcPositionManagerClient(
            repo=position_repo,
            journal_client=journal_client,
            alert_client=NoopAlertClient(),
        )
        execution_client = ExecutionServiceClient(execution_store, kill_switch_client, admission_repo, position_manager_client, db)

        candidate = seed_candidate(candidate_repo)

        approve_result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
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
        assert execution.status == "position_opened"
        assert position is not None


@pytest.mark.asyncio
async def test_pipeline_execution_failure_rolls_back_candidate_and_writes_journal():
    session_factory = make_session_factory()
    with session_factory() as db:
        correlation_id = "corr_e2e_fail"
        candidate_repo = TradeCandidateRepository(db)
        operator_action_repo = OperatorActionRepository(db)
        execution_client = DummyExecutionClient(ok=False, execution_id=None)
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)

        candidate = seed_candidate(candidate_repo)

        result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
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
        execution_client = DummyExecutionClient(ok=True, execution_id="exe_001")
        kill_switch_client = StubKillSwitchClient(trading_enabled=False, incident_code="manual_halt")

        candidate = seed_candidate(candidate_repo)

        result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
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
        assert len(journal_rows) == 1
        assert journal_rows[0].event_type == "kill_switch_blocked"
        assert journal_rows[0].payload["candidate_id"] == candidate.candidate_id
        assert operator_rows == []


@pytest.mark.asyncio
async def test_pipeline_expired_candidate_blocks_approve_before_execution():
    session_factory = make_session_factory()
    with session_factory() as db:
        correlation_id = "corr_e2e_expired"
        candidate_repo = TradeCandidateRepository(db)
        operator_action_repo = OperatorActionRepository(db)
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
        admission_repo = DbPositionAdmissionRepo(db)
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)
        position_manager_client = InProcPositionManagerClient(
            repo=position_repo,
            journal_client=journal_client,
            alert_client=NoopAlertClient(),
        )
        execution_client = ExecutionServiceClient(
            execution_store,
            kill_switch_client,
            admission_repo,
            position_manager_client,
            db,
        )

        candidate = seed_candidate(candidate_repo)

        result = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=operator_action_repo,
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
        assert execution.status == "position_opened"
        assert position is not None
        assert paper_event is not None
        assert execution_client.calls == 1


class InProcessEvaluateClient:
    def __init__(self, repo: TradeCandidateRepository) -> None:
        self.repo = repo

    async def evaluate(self, payload) -> dict:
        result = evaluate_pipeline_use_case(
            repo=self.repo,
            signal=payload.signal,
            risk=payload.risk,
            review=payload.review,
            correlation_id=payload.correlation_id,
        )
        return {"ok": result["ok"], "data": result, "error": None}


class StaticMarketFetcher:
    def __init__(self, candles: list[dict]) -> None:
        self.candles = candles

    def fetch_candles(self, symbol: str, timeframe: str, limit: int) -> list[dict]:
        _ = (symbol, timeframe)
        return self.candles[:limit]


def deterministic_candles() -> list[dict]:
    end = datetime.now(timezone.utc) - timedelta(seconds=5)
    start = end - timedelta(minutes=15 * 59)
    return [
        {
            "timestamp": start + timedelta(minutes=15 * index),
            "open": 100.0 + index,
            "high": 101.0 + index,
            "low": 99.0 + index,
            "close": 100.5 + index,
            "session": "paper_e2e",
        }
        for index in range(60)
    ]


def deterministic_signal() -> SignalDecision:
    return SignalDecision(
        signal_id="sig_deterministic_e2e",
        status=SignalStatus.CANDIDATE,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        setup_type="deterministic_fixture",
        entry_zone=EntryZone(min=100.0, max=102.0),
        stop_loss=95.0,
        take_profit=[110.0],
        confidence=0.75,
        invalidation=None,
        reasoning_summary="fixed integration fixture",
    )


def deterministic_risk() -> RiskDecision:
    return RiskDecision(
        risk_id="risk_deterministic_e2e",
        signal_id="sig_deterministic_e2e",
        symbol="BTCUSDT",
        approved=True,
        position_size=1.0,
        notional_usdt=101.0,
        max_loss_usdt=6.0,
        risk_pct_of_equity=0.6,
        entry_price=101.0,
        leverage=1.0,
        portfolio_exposure_pct=10.1,
        daily_loss_limit_status="ok",
        drawdown_lock=False,
        kill_switch_required=False,
        reason_codes=[RiskReasonCode.RISK_OK],
    )


def deterministic_review() -> ReviewDecision:
    return ReviewDecision(
        review_id="review_deterministic_e2e",
        signal_id="sig_deterministic_e2e",
        risk_id="risk_deterministic_e2e",
        passed=True,
        anomaly_flags=[],
        review_notes="fixed integration fixture",
        execution_candidate=ExecutionCandidate(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type="limit",
            entry_price=101.0,
            quantity=1.0,
            stop_loss=95.0,
            take_profit=[110.0],
            time_in_force="GTC",
        ),
    )


@pytest.mark.asyncio
async def test_deterministic_paper_lifecycle_persists_closed_position(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("ops.paper_pipeline_runner.uuid4", lambda: UUID(int=1))
    monkeypatch.setattr("apps.orchestrator.application.create_candidate.uuid4", lambda: UUID(int=2))
    monkeypatch.setattr("apps.execution_service.application.place_order_dry_run.uuid4", lambda: UUID(int=3))
    position_ids = iter(UUID(int=value) for value in range(4, 12))
    monkeypatch.setattr(
        "apps.position_manager.infrastructure.position_repo.uuid4",
        lambda: next(position_ids),
    )

    session_factory = make_session_factory()
    with session_factory() as db:
        candidate_repo = TradeCandidateRepository(db)
        position_repo = PositionRepository(db)
        journal_client = DbJournalClient(db)
        kill_switch_client = StubKillSwitchClient(trading_enabled=True)
        execution_client = ExecutionServiceClient(
            DbExecutionStore(db),
            kill_switch_client,
            DbPositionAdmissionRepo(db),
            InProcPositionManagerClient(
                repo=position_repo,
                journal_client=journal_client,
                alert_client=NoopAlertClient(),
            ),
            db,
        )

        cycle = await run_cycle(
            symbol="BTCUSDT",
            timeframe="15m",
            candle_limit=60,
            kill_switch_client=kill_switch_client,
            market_fetcher=StaticMarketFetcher(deterministic_candles()),
            evaluate_client=InProcessEvaluateClient(candidate_repo),
            account_state=PaperHarnessAccountState(
                equity_usdt=1000.0,
                daily_pnl_usdt=0.0,
                portfolio_exposure_pct=0.0,
                open_positions=0,
            ),
            signal_evaluator=lambda snapshot: deterministic_signal(),
            risk_evaluator=lambda request: deterministic_risk().model_dump(
                mode="python",
                exclude={"risk_id", "signal_id", "symbol"},
            ),
            review_evaluator=lambda signal, risk, snapshot, stale_threshold_seconds: deterministic_review(),
        )

        assert cycle["candidate_created"] is True
        assert cycle["correlation_id"] == "corr_paper_pipeline_00000000000000000000000000000001"

        candidate = candidate_repo.get_by_signal_id("sig_deterministic_e2e")
        assert candidate is not None

        approval = await approve_candidate_use_case(
            repo=candidate_repo,
            kill_switch_client=kill_switch_client,
            execution_client=execution_client,
            operator_action_repo=OperatorActionRepository(db),
            candidate_id=candidate.candidate_id,
            telegram_user_id=123,
            correlation_id=cycle["correlation_id"],
        )
        assert approval["ok"] is True

        position = position_repo.get_by_execution_id(approval["execution_id"])
        assert position is not None
        close_result = await close_position_use_case(
            repo=position_repo,
            journal_client=journal_client,
            alert_client=NoopAlertClient(),
            req=PositionCloseRequest(
                position_id=position.position_id,
                reason=PositionCloseReason.TAKE_PROFIT,
                close_price=110.0,
                closed_at=datetime.now(timezone.utc),
                correlation_id=cycle["correlation_id"],
            ),
        )
        assert close_result["ok"] is True

        candidate_id = candidate.candidate_id
        execution_id = approval["execution_id"]
        position_id = position.position_id

    with session_factory() as restarted_db:
        persisted_candidate = restarted_db.get(TradeCandidateModel, candidate_id)
        persisted_execution = restarted_db.get(ExecutionModel, execution_id)
        persisted_position = restarted_db.get(PositionModel, position_id)
        position_events = restarted_db.execute(
            select(PositionEventModel).where(PositionEventModel.position_id == position_id)
        ).scalars().all()

        assert persisted_candidate is not None
        assert persisted_candidate.status == "submitted"
        assert persisted_execution is not None
        assert persisted_execution.status == "position_opened"
        assert persisted_position is not None
        assert persisted_position.status == "closed"
        assert persisted_position.close_reason == "take_profit"
        assert persisted_position.close_price == 110.0
        assert [event.event_type for event in position_events] == [
            "position_opened",
            "position_closed",
        ]
