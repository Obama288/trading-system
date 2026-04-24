from __future__ import annotations

import os
from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.kill_switch.main import app
from apps.orchestrator.application.approve_candidate import approve_candidate_use_case
from apps.orchestrator.infrastructure.candidate_repo import TradeCandidateRepository
from libs.db.base import Base
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.operator_action import OperatorActionModel
from libs.db.models.system_state import SystemStateModel
from libs.db.models.trade_candidate import TradeCandidateModel
from libs.db.session import get_db

TEST_ADMIN_TOKEN = "test-admin-token-001"


class DummyExecutionClient:
    def __init__(self) -> None:
        self.calls = 0

    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict:
        self.calls += 1
        return {
            "ok": True,
            "data": {"execution_id": "exe_resume_001"},
            "error": None,
        }


class DummyJournalClient:
    def __init__(self) -> None:
        self.writes: list[dict] = []

    async def write(self, payload: dict) -> None:
        self.writes.append(payload)


class DummyOperatorActionRepo:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, **kwargs):
        self.records.append(kwargs)
        return kwargs

    def record_no_commit(self, **kwargs):
        self.records.append(kwargs)
        return kwargs


class DbBackedKillSwitchClient:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    async def get_status(self, correlation_id: str) -> dict:
        from apps.kill_switch.application.get_status import get_kill_switch_status_use_case
        from apps.kill_switch.infrastructure.system_state_repo import SystemStateRepository

        with self.session_factory() as db:
            state = get_kill_switch_status_use_case(SystemStateRepository(db))
        return {
            "ok": True,
            "service": "kill-switch",
            "version": "v1",
            "correlation_id": correlation_id,
            "data": state,
            "error": None,
        }


class ResumeAwareTradeCandidateRepository(TradeCandidateRepository):
    def expire_if_needed(self, model):
        if model.ttl_expires_at is not None and model.ttl_expires_at.tzinfo is None:
            model.ttl_expires_at = model.ttl_expires_at.replace(tzinfo=timezone.utc)
        return super().expire_if_needed(model)


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


def seed_candidate(session_factory: sessionmaker[Session]) -> None:
    now = datetime.now(timezone.utc)
    with session_factory() as db:
        db.add(
            TradeCandidateModel(
                candidate_id="cand_resume_001",
                signal_id="sig_resume_001",
                risk_id="risk_resume_001",
                review_id="rev_resume_001",
                symbol="BTCUSDT",
                side="long",
                status="pending",
                execution_payload_json={"symbol": "BTCUSDT", "side": "buy"},
                ttl_expires_at=now + timedelta(minutes=5),
                approved_by_user_id=None,
                approved_at=None,
                rejected_by_user_id=None,
                rejected_at=None,
                execution_id=None,
                created_at=now,
            )
        )
        db.commit()


def test_resume_endpoint_changes_state_and_writes_audit_and_journal():
    client, session_factory = make_client()
    try:
        response = client.post(
            "/v1/kill-switch/resume",
            json={
                "operator_user_id": 123,
                "actor": "paper-ops",
                "correlation_id": "corr_resume_001",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["correlation_id"] == "corr_resume_001"
        assert body["data"]["trading_enabled"] is True
        assert body["data"]["kill_switch_active"] is False
        assert body["data"]["incident_code"] == "paper_mode_resumed"

        with session_factory() as db:
            state_row = db.get(SystemStateModel, "kill_switch_state")
            trading_enabled_row = db.get(SystemStateModel, "trading_enabled")
            operator_action = db.execute(select(OperatorActionModel)).scalar_one()
            journal_event = db.execute(select(JournalEventModel)).scalar_one()

        assert state_row is not None
        assert state_row.value_json == {
            "trading_enabled": True,
            "kill_switch_active": False,
            "incident_code": "paper_mode_resumed",
        }
        assert trading_enabled_row is not None
        assert trading_enabled_row.value_json == {"value": True}
        assert operator_action.action_type == "kill_switch_resume"
        assert operator_action.target_type == "system_state"
        assert operator_action.target_id == "kill_switch_state"
        assert operator_action.correlation_id == "corr_resume_001"
        assert operator_action.payload_json == {
            "actor": "paper-ops",
            "result": "resumed",
        }
        assert journal_event.event_type == "kill_switch_resumed"
        assert journal_event.correlation_id == "corr_resume_001"
        assert journal_event.payload == {
            "operator_user_id": 123,
            "actor": "paper-ops",
            "result": "resumed",
        }
    finally:
        teardown_client(client)


@pytest.mark.asyncio
async def test_resume_unblocks_approve_flow():
    client, session_factory = make_client()
    try:
        seed_candidate(session_factory)
        response = client.post(
            "/v1/kill-switch/resume",
            json={
                "operator_user_id": 123,
                "actor": "paper-ops",
                "correlation_id": "corr_resume_approve",
            },
        )
        assert response.status_code == 200

        with session_factory() as db:
            repo = ResumeAwareTradeCandidateRepository(db)
            result = await approve_candidate_use_case(
                repo=repo,
                kill_switch_client=DbBackedKillSwitchClient(session_factory),
                execution_client=DummyExecutionClient(),
                operator_action_repo=DummyOperatorActionRepo(),
                candidate_id="cand_resume_001",
                telegram_user_id=123,
                correlation_id="corr_resume_approve",
            )

            candidate = repo.get_candidate("cand_resume_001")

        assert result["ok"] is True
        assert result["code"] == "APPROVED"
        assert candidate is not None
        assert candidate.status == "submitted"
        assert candidate.execution_id == "exe_resume_001"
    finally:
        teardown_client(client)
