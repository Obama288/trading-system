from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.execution_service.application.detect_orphans import detect_orphan_executions_use_case_async
from libs.db.base import Base
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.execution import ExecutionModel
from libs.messaging.journal_client import DbJournalClient


class MockOrphanExecution:
    def __init__(self, execution_id: str, candidate_id: str, status: str, mode: str):
        self.execution_id = execution_id
        self.idempotency_key = f"idem_{execution_id}"
        self.candidate_id = candidate_id
        self.status = status
        self.mode = mode
        self.payload = {"symbol": "BTCUSDT"}
        self.created_at = "2026-01-01T00:00:00"


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def db_with_orphan_execution(db_session):
    exec_model = ExecutionModel(
        execution_id="exec_orphan_001",
        idempotency_key="idem_orphan_001",
        candidate_id="cand_001",
        status="pending_open",
        mode="paper",
        payload={"symbol": "BTCUSDT", "side": "buy"},
    )
    db_session.add(exec_model)
    db_session.commit()
    return db_session


@pytest.mark.asyncio
async def test_orphan_detection_writes_journal_event_to_db(db_with_orphan_execution):
    journal_calls = []

    class TestDetector:
        def get_pending_open_executions(self, mode=None):
            return [MockOrphanExecution("exec_orphan_001", "cand_001", "pending_open", "paper")]

        def get_emitted_orphan_event_ids(self):
            return set()

        async def emit_detection_event(self, events):
            journal_calls.extend(events)

        async def emit_escalation_event(self, count):
            pass

        def get_correlation_id(self):
            return "corr_test"

    await detect_orphan_executions_use_case_async(
        detector=TestDetector(),
        mode="paper",
        emit_events=True,
    )

    assert len(journal_calls) == 1
    db_journal = DbJournalClient(db_with_orphan_execution)
    await db_journal.write(journal_calls[0])

    stmt = select(JournalEventModel).where(
        JournalEventModel.event_type == "orphan_execution_detected"
    )
    result = db_with_orphan_execution.execute(stmt).scalars().all()

    assert len(result) == 1
    event = result[0]
    assert event.event_type == "orphan_execution_detected"
    assert "exec_orphan_001" in event.event_id


@pytest.mark.asyncio
async def test_orphan_detection_dedup_against_db_event(db_with_orphan_execution):
    existing_event = JournalEventModel(
        event_id="evt_orphan_execution_detected_exec_orphan_001",
        event_type="orphan_execution_detected",
        severity="warning",
        correlation_id="corr_test",
        payload={"execution_id": "exec_orphan_001"},
    )
    db_with_orphan_execution.add(existing_event)
    db_with_orphan_execution.commit()

    detection_count = [0]

    class TestDetector:
        def get_pending_open_executions(self, mode=None):
            return [MockOrphanExecution("exec_orphan_001", "cand_001", "pending_open", "paper")]

        def get_emitted_orphan_event_ids(self):
            stmt = select(JournalEventModel.event_id).where(
                JournalEventModel.event_type == "orphan_execution_detected"
            )
            return set(db_with_orphan_execution.execute(stmt).scalars().all())

        async def emit_detection_event(self, events):
            detection_count[0] += len(events)

        async def emit_escalation_event(self, count):
            pass

        def get_correlation_id(self):
            return "corr_test"

    result = await detect_orphan_executions_use_case_async(
        detector=TestDetector(),
        mode="paper",
        emit_events=True,
    )

    assert result["new_orphan_count"] == 0
    assert result["already_signaled_count"] == 1
    assert detection_count[0] == 0