from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.journal_ingest.main import app
from libs.db.base import Base
from libs.db.models.journal_event import JournalEventModel
from libs.db.session import get_db


def make_client() -> tuple[TestClient, sessionmaker[Session]]:
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
    return TestClient(app), test_session_factory


def teardown_client(client: TestClient) -> None:
    client.close()
    app.dependency_overrides.clear()


def test_write_event_persists_to_database():
    client, session_factory = make_client()
    try:
        response = client.post(
            "/v1/journal/events",
            json={
                "event_id": "evt_001",
                "event_type": "candidate_created",
                "severity": "info",
                "correlation_id": "corr_001",
                "payload": {"candidate_id": "cand_001"},
            },
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True, "event_id": "evt_001"}

        with session_factory() as db:
            row = db.get(JournalEventModel, "evt_001")
            assert row is not None
            assert row.event_type == "candidate_created"
            assert row.severity == "info"
            assert row.correlation_id == "corr_001"
            assert row.payload == {"candidate_id": "cand_001"}
    finally:
        teardown_client(client)


def test_query_events_returns_persisted_rows_with_filters():
    client, _session_factory = make_client()
    try:
        payloads = [
            {
                "event_id": "evt_001",
                "event_type": "candidate_created",
                "severity": "info",
                "correlation_id": "corr_a",
                "payload": {"candidate_id": "cand_001"},
            },
            {
                "event_id": "evt_002",
                "event_type": "candidate_approved",
                "severity": "warning",
                "correlation_id": "corr_b",
                "payload": {"candidate_id": "cand_002"},
            },
            {
                "event_id": "evt_003",
                "event_type": "candidate_created",
                "severity": "info",
                "correlation_id": "corr_a",
                "payload": {"candidate_id": "cand_003"},
            },
        ]

        for payload in payloads:
            response = client.post("/v1/journal/events", json=payload)
            assert response.status_code == 200

        response = client.get(
            "/v1/journal/events",
            params={"event_type": "candidate_created", "correlation_id": "corr_a"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["total"] == 2
        assert len(body["items"]) == 2
        assert {item["event_id"] for item in body["items"]} == {"evt_001", "evt_003"}
        assert all(item["event_type"] == "candidate_created" for item in body["items"])
        assert all(item["correlation_id"] == "corr_a" for item in body["items"])
        assert all("created_at" in item for item in body["items"])
    finally:
        teardown_client(client)
