from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.position_manager.application.close_position import close_position_use_case
from apps.position_manager.application.open_position import open_position_use_case
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionCloseRequest, PositionOpenRequest
from libs.db.base import Base
from libs.schemas.common import ExecutionStatus, PositionCloseReason, TradeDirection


@pytest.fixture()
def test_db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


def _make_req(execution_id: str = "exe_001") -> PositionOpenRequest:
    return PositionOpenRequest(
        execution_id=execution_id,
        execution_status=ExecutionStatus.FILLED,
        symbol="BTC-USDT",
        side=TradeDirection.LONG,
        quantity=0.1,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=[51000.0],
        opened_at=datetime.now(timezone.utc),
        candidate_id="cand_001",
        signal_id=None,
        correlation_id="corr_001",
    )


class _NoopJournalClient:
    async def write(self, event: dict) -> None:
        pass


class _FailingJournalClient:
    async def write(self, event: dict) -> None:
        raise RuntimeError("journal service unavailable")


class _FailingAlertClient:
    async def notify(self, payload: dict) -> None:
        raise RuntimeError("alerts service unavailable")


class _NoopAlertClient:
    async def notify(self, payload: dict) -> None:
        pass


class TestOpenPositionUseCase:
    @pytest.mark.asyncio
    async def test_happy_path(self, test_db):
        repo = PositionRepository(test_db)
        result = await open_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=_make_req("exe_happy"),
        )
        assert result["ok"] is True
        assert result["code"] == "POSITION_OPENED"
        assert repo.get_by_execution_id("exe_happy") is not None

    @pytest.mark.asyncio
    async def test_alert_failure_does_not_fail_position_open(self, test_db):
        repo = PositionRepository(test_db)
        result = await open_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_FailingAlertClient(),
            req=_make_req("exe_alert_fail"),
        )
        assert result["ok"] is True
        assert result["code"] == "POSITION_OPENED"
        assert repo.get_by_execution_id("exe_alert_fail") is not None

    @pytest.mark.asyncio
    async def test_idempotent_on_existing_position(self, test_db):
        repo = PositionRepository(test_db)
        req = _make_req("exe_idem")
        await open_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=req,
        )
        result = await open_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=req,
        )
        assert result["ok"] is True
        assert result["code"] == "POSITION_EXISTS"

    @pytest.mark.asyncio
    async def test_journal_failure_does_not_fail_position_open(self, test_db):
        repo = PositionRepository(test_db)
        result = await open_position_use_case(
            repo=repo,
            journal_client=_FailingJournalClient(),
            alert_client=_NoopAlertClient(),
            req=_make_req("exe_journal_fail"),
        )
        assert result["ok"] is True
        assert result["code"] == "POSITION_OPENED"
        assert repo.get_by_execution_id("exe_journal_fail") is not None

    @pytest.mark.asyncio
    async def test_rejects_unfilled_execution(self, test_db):
        repo = PositionRepository(test_db)
        req = _make_req("exe_not_filled")
        req = req.model_copy(update={"execution_status": ExecutionStatus.CANCELLED})
        result = await open_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=req,
        )
        assert result["ok"] is False
        assert result["code"] == "EXECUTION_NOT_FILLED"


async def _open_position(test_db: Session, execution_id: str) -> str:
    """Helper: open a position and return its position_id."""
    repo = PositionRepository(test_db)
    result = await open_position_use_case(
        repo=repo,
        journal_client=_NoopJournalClient(),
        alert_client=_NoopAlertClient(),
        req=_make_req(execution_id),
    )
    return result["position"]["position_id"]


def _make_close_req(position_id: str) -> PositionCloseRequest:
    return PositionCloseRequest(
        position_id=position_id,
        reason=PositionCloseReason.MANUAL,
        close_price=51000.0,
        closed_at=datetime.now(timezone.utc),
        correlation_id="corr_close_001",
    )


class TestClosePositionUseCase:
    @pytest.mark.asyncio
    async def test_happy_path(self, test_db):
        position_id = await _open_position(test_db, "exe_close_happy")
        repo = PositionRepository(test_db)
        result = await close_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=_make_close_req(position_id),
        )
        assert result["ok"] is True
        assert result["code"] == "POSITION_CLOSED"
        row = repo.get_position(position_id)
        assert row is not None
        assert row.status == "closed"

    @pytest.mark.asyncio
    async def test_journal_failure_does_not_fail_position_close(self, test_db):
        position_id = await _open_position(test_db, "exe_close_journal_fail")
        repo = PositionRepository(test_db)
        result = await close_position_use_case(
            repo=repo,
            journal_client=_FailingJournalClient(),
            alert_client=_NoopAlertClient(),
            req=_make_close_req(position_id),
        )
        assert result["ok"] is True
        assert result["code"] == "POSITION_CLOSED"
        row = repo.get_position(position_id)
        assert row is not None
        assert row.status == "closed"

    @pytest.mark.asyncio
    async def test_alert_failure_does_not_fail_position_close(self, test_db):
        position_id = await _open_position(test_db, "exe_close_alert_fail")
        repo = PositionRepository(test_db)
        result = await close_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_FailingAlertClient(),
            req=_make_close_req(position_id),
        )
        assert result["ok"] is True
        assert result["code"] == "POSITION_CLOSED"
        row = repo.get_position(position_id)
        assert row.status == "closed"

    @pytest.mark.asyncio
    async def test_not_found(self, test_db):
        repo = PositionRepository(test_db)
        result = await close_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=_make_close_req("pos_nonexistent"),
        )
        assert result["ok"] is False
        assert result["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_already_closed_rejected(self, test_db):
        position_id = await _open_position(test_db, "exe_double_close")
        repo = PositionRepository(test_db)
        await close_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=_make_close_req(position_id),
        )
        result = await close_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            req=_make_close_req(position_id),
        )
        assert result["ok"] is False
        assert result["code"] == "POSITION_NOT_OPEN"
