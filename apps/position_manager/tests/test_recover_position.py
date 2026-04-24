from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.position_manager.application.recover_position import recover_position_use_case
from apps.position_manager.infrastructure.position_repo import PositionRepository
from libs.db.base import Base
from libs.db.models.execution import ExecutionModel
from libs.db.models.position import PositionModel


@pytest.fixture()
def test_db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class _NoopJournalClient:
    async def write(self, event):
        pass


class _NoopAlertClient:
    async def notify(self, alert):
        pass


def _make_execution(db, execution_id: str, candidate_id: str = "cand_001", mode: str = "paper"):
    row = ExecutionModel(
        execution_id=execution_id,
        idempotency_key=f"idem_{execution_id}",
        candidate_id=candidate_id,
        status="filled",
        mode=mode,
        payload={
            "symbol": "BTC-USDT",
            "side": "long",
            "entry_price": 50000.0,
            "quantity": 0.1,
            "stop_loss": 49000.0,
            "take_profit": [51000.0],
            "candidate_id": candidate_id,
        },
    )
    db.add(row)
    db.commit()
    return row


class TestRecoverPositionUseCase:
    @pytest.mark.asyncio
    async def test_recover_creates_position_from_filled_execution(self, test_db):
        execution_id = "exe_recover_001"
        _make_execution(test_db, execution_id)

        repo = PositionRepository(test_db)

        result = await recover_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            execution_id=execution_id,
            correlation_id="corr_recover_001",
        )

        assert result["ok"] is True
        assert result["code"] == "POSITION_RECOVERED"
        position = result["position"]
        assert position["execution_id"] == execution_id
        assert position["symbol"] == "BTC-USDT"
        assert position["status"] == "open"

        persisted = repo.get_by_execution_id(execution_id)
        assert persisted is not None
        assert persisted.position_id == position["position_id"]

    @pytest.mark.asyncio
    async def test_recover_is_idempotent_on_existing_position(self, test_db):
        execution_id = "exe_recover_002"
        _make_execution(test_db, execution_id)

        repo = PositionRepository(test_db)

        result1 = await recover_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            execution_id=execution_id,
            correlation_id="corr_recover_002",
        )
        assert result1["code"] == "POSITION_RECOVERED"

        result2 = await recover_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            execution_id=execution_id,
            correlation_id="corr_recover_002b",
        )
        assert result2["ok"] is True
        assert result2["code"] == "POSITION_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_recover_fails_when_execution_not_found(self, test_db):
        repo = PositionRepository(test_db)

        result = await recover_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            execution_id="exe_nonexistent",
            correlation_id="corr_003",
        )

        assert result["ok"] is False
        assert result["code"] == "EXECUTION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_recover_fails_when_execution_not_filled(self, test_db):
        execution_id = "exe_not_filled"
        row = ExecutionModel(
            execution_id=execution_id,
            idempotency_key=f"idem_{execution_id}",
            candidate_id="cand_003",
            status="cancelled",
            mode="paper",
            payload={},
        )
        test_db.add(row)
        test_db.commit()

        repo = PositionRepository(test_db)

        result = await recover_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_NoopAlertClient(),
            execution_id=execution_id,
            correlation_id="corr_004",
        )

        assert result["ok"] is False
        assert result["code"] == "EXECUTION_NOT_FILLED"

    @pytest.mark.asyncio
    async def test_journal_failure_does_not_fail_position_recovery(self, test_db):
        execution_id = "exe_recover_journal_fail"
        _make_execution(test_db, execution_id)

        repo = PositionRepository(test_db)

        class _FailingJournalClient:
            async def write(self, event):
                raise RuntimeError("journal service unavailable")

        result = await recover_position_use_case(
            repo=repo,
            journal_client=_FailingJournalClient(),
            alert_client=_NoopAlertClient(),
            execution_id=execution_id,
            correlation_id="corr_recover_journal_fail",
        )

        assert result["ok"] is True
        assert result["code"] == "POSITION_RECOVERED"
        persisted = repo.get_by_execution_id(execution_id)
        assert persisted is not None
        assert persisted.status == "open"

    @pytest.mark.asyncio
    async def test_alert_failure_does_not_fail_position_recovery(self, test_db):
        execution_id = "exe_recover_alert_fail"
        _make_execution(test_db, execution_id)

        repo = PositionRepository(test_db)

        class _FailingAlertClient:
            async def notify(self, payload):
                raise RuntimeError("alerts service unavailable")

        result = await recover_position_use_case(
            repo=repo,
            journal_client=_NoopJournalClient(),
            alert_client=_FailingAlertClient(),
            execution_id=execution_id,
            correlation_id="corr_recover_alert_fail",
        )

        assert result["ok"] is True
        assert result["code"] == "POSITION_RECOVERED"
        persisted = repo.get_by_execution_id(execution_id)
        assert persisted is not None
        assert persisted.status == "open"