from __future__ import annotations

import os
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.kill_switch.main import app
from libs.db.base import Base
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.operator_action import OperatorActionModel
from libs.db.models.system_state import SystemStateModel
from libs.db.session import get_db

TEST_ADMIN_TOKEN = "test-admin-token-halt-001"


def make_client() -> tuple[TestClient, sessionmaker[Session]]:
    os.environ["ADMIN_TOKEN"] = TEST_ADMIN_TOKEN
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    client.headers["X-Admin-Token"] = TEST_ADMIN_TOKEN
    return client, test_session_factory


def teardown_client(client: TestClient) -> None:
    client.close()
    app.dependency_overrides.clear()
    os.environ.pop("ADMIN_TOKEN", None)


def test_halt_commit_failure_leaves_no_partial_state(monkeypatch):
    """
    If the single DB commit fails, none of state/operator_action/journal_event
    should be partially persisted. SQLAlchemy rolls back the session on commit failure.

    Limitation: we cannot simulate a mid-write partial commit in SQLite since it
    uses a single connection with StaticPool. What we CAN prove is:
    - the commit is the only place writes are flushed to durable storage
    - if commit raises, the session rolls back and nothing persists
    This test patches Session.commit to raise, then verifies the DB is empty.
    raise_server_exceptions=False so TestClient returns 500 instead of re-raising.
    """
    os.environ["ADMIN_TOKEN"] = TEST_ADMIN_TOKEN
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    client.headers["X-Admin-Token"] = TEST_ADMIN_TOKEN
    try:
        original_commit = Session.commit

        def failing_commit(self):
            raise Exception("simulated DB failure on commit")

        monkeypatch.setattr(Session, "commit", failing_commit)

        response = client.post(
            "/v1/kill-switch/halt",
            json={
                "operator_user_id": 1,
                "reason": "commit_fail_test",
                "actor": "test",
                "correlation_id": "corr_commit_fail_halt",
            },
        )

        monkeypatch.setattr(Session, "commit", original_commit)

        assert response.status_code == 500

        with test_session_factory() as db:
            state = db.get(SystemStateModel, "kill_switch_state")
            op_count = db.execute(select(func.count()).select_from(OperatorActionModel)).scalar_one()
            j_count = db.execute(select(func.count()).select_from(JournalEventModel)).scalar_one()

        assert state is None, "kill_switch_state must not be persisted on commit failure"
        assert op_count == 0, "operator_action must not be persisted on commit failure"
        assert j_count == 0, "journal_event must not be persisted on commit failure"
    finally:
        client.close()
        app.dependency_overrides.clear()
        os.environ.pop("ADMIN_TOKEN", None)


def test_halt_endpoint_changes_state_and_writes_audit_and_journal():
    client, session_factory = make_client()
    try:
        response = client.post(
            "/v1/kill-switch/halt",
            json={
                "operator_user_id": 42,
                "reason": "emergency_stop",
                "actor": "paper-ops",
                "correlation_id": "corr_halt_001",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["correlation_id"] == "corr_halt_001"
        assert body["data"]["trading_enabled"] is False
        assert body["data"]["kill_switch_active"] is True
        assert body["data"]["incident_code"] == "emergency_stop"

        with session_factory() as db:
            state_row = db.get(SystemStateModel, "kill_switch_state")
            trading_enabled_row = db.get(SystemStateModel, "trading_enabled")
            operator_action = db.execute(select(OperatorActionModel)).scalar_one()
            journal_event = db.execute(select(JournalEventModel)).scalar_one()

        assert state_row is not None
        assert state_row.value_json == {
            "trading_enabled": False,
            "kill_switch_active": True,
            "incident_code": "emergency_stop",
        }
        assert trading_enabled_row is not None
        assert trading_enabled_row.value_json == {"value": False}

        assert operator_action.action_type == "kill_switch_halt"
        assert operator_action.target_type == "system_state"
        assert operator_action.target_id == "kill_switch_state"
        assert operator_action.correlation_id == "corr_halt_001"
        assert operator_action.payload_json == {
            "reason": "emergency_stop",
            "actor": "paper-ops",
            "result": "halted",
        }

        assert journal_event.event_type == "kill_switch_halted"
        assert journal_event.severity == "warning"
        assert journal_event.correlation_id == "corr_halt_001"
        assert journal_event.payload == {
            "operator_user_id": 42,
            "actor": "paper-ops",
            "reason": "emergency_stop",
            "result": "halted",
        }
    finally:
        teardown_client(client)
