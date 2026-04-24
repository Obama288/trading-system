from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.execution_service.application.detect_orphans import detect_orphan_executions_use_case_sync, OrphanExecution
from apps.execution_service.infrastructure.position_admission_repo import DbPositionAdmissionRepo
from libs.db.base import Base
from libs.db.models.execution import ExecutionModel


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


class FakeDetector:
    def __init__(self, orphans, emitted_ids=None):
        self.orphans = orphans
        self.emitted_ids = emitted_ids or set()
        self.emitted_events = []
        self.escalation_count = 0

    def get_pending_open_executions(self, mode=None):
        return self.orphans

    def get_emitted_orphan_event_ids(self) -> set[str]:
        return self.emitted_ids

    def emit_detection_event(self, events):
        self.emitted_events.extend(events)

    def emit_escalation_event(self, count):
        self.escalation_count = count

    def get_correlation_id(self):
        return "corr_test"

    def get_journal_client(self):
        return None


class TestDetectOrphanExecutionsUseCase:
    def test_detect_returns_empty_when_no_orphans(self, test_db):
        detector = FakeDetector([])
        result = detect_orphan_executions_use_case_sync(
            detector=detector,
            mode="paper",
            emit_events=False,
        )

        assert result["ok"] is True
        assert result["orphan_count"] == 0
        assert result["execution_ids"] == []

    def test_detect_returns_orphans_when_exist(self, test_db):
        exec1 = ExecutionModel(
            execution_id="exe_orphan_001",
            idempotency_key="idem_001",
            candidate_id="cand_001",
            status="filled",
            mode="paper",
            payload={"symbol": "BTC-USDT", "side": "long", "quantity": 0.1},
        )
        exec2 = ExecutionModel(
            execution_id="exe_orphan_002",
            idempotency_key="idem_002",
            candidate_id="cand_002",
            status="filled",
            mode="paper",
            payload={"symbol": "ETH-USDT", "side": "short", "quantity": 1.0},
        )
        test_db.add(exec1)
        test_db.add(exec2)
        test_db.commit()

        admission_repo = DbPositionAdmissionRepo(test_db)

        class Detector:
            def get_pending_open_executions(self, mode=None):
                return admission_repo.get_pending_open_executions(mode=mode)

            def get_emitted_orphan_event_ids(self) -> set[str]:
                return set()

            def emit_detection_event(self, events):
                pass

            def emit_escalation_event(self, count):
                pass

            def get_correlation_id(self):
                return "corr_test"

            def get_journal_client(self):
                return None

        result = detect_orphan_executions_use_case_sync(
            detector=Detector(),
            mode="paper",
            emit_events=False,
        )

        assert result["orphan_count"] == 2
        assert "exe_orphan_001" in result["execution_ids"]
        assert "exe_orphan_002" in result["execution_ids"]

    def test_detect_emits_events_when_orphans_exist(self, test_db):
        exec1 = ExecutionModel(
            execution_id="exe_event_001",
            idempotency_key="idem_event_001",
            candidate_id="cand_001",
            status="filled",
            mode="paper",
            payload={},
        )
        test_db.add(exec1)
        test_db.commit()

        admission_repo = DbPositionAdmissionRepo(test_db)

        class Detector:
            def get_pending_open_executions(self, mode=None):
                return admission_repo.get_pending_open_executions(mode=mode)

            def get_emitted_orphan_event_ids(self) -> set[str]:
                return set()

            def emit_detection_event(self, events):
                self.emitted = events

            def emit_escalation_event(self, count):
                self.escalation_count = count

            def get_correlation_id(self):
                return "corr_test"

            def get_journal_client(self):
                return None

        detector = Detector()
        result = detect_orphan_executions_use_case_sync(
            detector=detector,
            mode="paper",
            emit_events=True,
        )

        assert result["orphan_count"] == 1
        assert hasattr(detector, "emitted")
        assert len(detector.emitted) == 1
        assert detector.emitted[0]["event_type"] == "orphan_execution_detected"

    def test_detect_filters_by_mode(self, test_db):
        exec_paper = ExecutionModel(
            execution_id="exe_paper",
            idempotency_key="idem_paper",
            candidate_id="cand_001",
            status="filled",
            mode="paper",
            payload={},
        )
        exec_live = ExecutionModel(
            execution_id="exe_live",
            idempotency_key="idem_live",
            candidate_id="cand_002",
            status="filled",
            mode="live",
            payload={},
        )
        test_db.add(exec_paper)
        test_db.add(exec_live)
        test_db.commit()

        admission_repo = DbPositionAdmissionRepo(test_db)

        class Detector:
            def get_pending_open_executions(self, mode=None):
                return admission_repo.get_pending_open_executions(mode=mode)

            def get_emitted_orphan_event_ids(self) -> set[str]:
                return set()

            def emit_detection_event(self, events):
                pass

            def emit_escalation_event(self, count):
                pass

            def get_correlation_id(self):
                return "corr_test"

            def get_journal_client(self):
                return None

        result = detect_orphan_executions_use_case_sync(
            detector=Detector(),
            mode="paper",
            emit_events=False,
        )

        assert result["orphan_count"] == 1
        assert result["execution_ids"][0] == "exe_paper"

    def test_detect_avoids_duplicate_events(self, test_db):
        exec1 = ExecutionModel(
            execution_id="exe_dup_001",
            idempotency_key="idem_dup_001",
            candidate_id="cand_001",
            status="filled",
            mode="paper",
            payload={},
        )
        test_db.add(exec1)
        test_db.commit()

        admission_repo = DbPositionAdmissionRepo(test_db)

        class Detector:
            def get_pending_open_executions(self, mode=None):
                return admission_repo.get_pending_open_executions(mode=mode)

            def get_emitted_orphan_event_ids(self) -> set[str]:
                return {"evt_orphan_execution_detected_exe_dup_001"}

            def emit_detection_event(self, events):
                self.emitted = events

            def emit_escalation_event(self, count):
                self.escalation_count = count

            def get_correlation_id(self):
                return "corr_test"

            def get_journal_client(self):
                return None

        detector = Detector()
        result = detect_orphan_executions_use_case_sync(
            detector=detector,
            mode="paper",
            emit_events=True,
        )

        assert result["orphan_count"] == 1
        assert result["new_orphan_count"] == 0
        assert result["already_signaled_count"] == 1
        assert not hasattr(detector, "emitted") or len(detector.emitted) == 0