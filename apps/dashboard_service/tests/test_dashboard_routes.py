from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.dashboard_service.main import app
from libs.db.base import Base
from libs.db.models.execution import ExecutionModel
from libs.db.models.incident import IncidentModel
from libs.db.models.journal_event import JournalEventModel
from libs.db.models.position import PositionModel
from libs.db.models.system_state import SystemStateModel
from libs.db.models.trade_candidate import TradeCandidateModel
from libs.db.session import get_db
from libs.schemas.common import PositionStatus


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


def seed_dashboard_rows(session_factory: sessionmaker[Session]) -> None:
    now = datetime.now(timezone.utc)
    with session_factory() as db:
        db.add(
            SystemStateModel(
                key="kill_switch_state",
                value_json={"kill_switch_active": False, "incident_code": None},
                updated_at=now,
                updated_by="tester",
            )
        )
        db.add_all(
            [
                TradeCandidateModel(
                    candidate_id="cand_001",
                    signal_id="sig_001",
                    risk_id="risk_001",
                    review_id="rev_001",
                    symbol="BTCUSDT",
                    side="long",
                    status="pending",
                    execution_payload_json={"symbol": "BTCUSDT", "setup_type": "breakout_retest"},
                    ttl_expires_at=now + timedelta(minutes=15),
                    approved_by_user_id=None,
                    approved_at=None,
                    rejected_by_user_id=None,
                    rejected_at=None,
                    execution_id=None,
                    created_at=now,
                ),
                TradeCandidateModel(
                    candidate_id="cand_002",
                    signal_id="sig_002",
                    risk_id="risk_002",
                    review_id="rev_002",
                    symbol="ETHUSDT",
                    side="short",
                    status="approved",
                    execution_payload_json={"symbol": "ETHUSDT", "setup_type": "trend_continuation"},
                    ttl_expires_at=now + timedelta(minutes=10),
                    approved_by_user_id=123,
                    approved_at=now,
                    rejected_by_user_id=None,
                    rejected_at=None,
                    execution_id="exe_002",
                    created_at=now - timedelta(minutes=5),
                ),
            ]
        )
        db.add_all(
            [
                ExecutionModel(
                    execution_id="exe_001",
                    idempotency_key="idem_001",
                    candidate_id="cand_001",
                    status="filled",
                    mode="paper",
                    payload={"symbol": "BTCUSDT"},
                    created_at=now - timedelta(hours=1),
                    updated_at=now - timedelta(hours=1),
                ),
                ExecutionModel(
                    execution_id="exe_002",
                    idempotency_key="idem_002",
                    candidate_id="cand_002",
                    status="filled",
                    mode="paper",
                    payload={"symbol": "ETHUSDT"},
                    created_at=now - timedelta(days=2),
                    updated_at=now - timedelta(days=1),
                ),
                ExecutionModel(
                    execution_id="exe_003",
                    idempotency_key="idem_003",
                    candidate_id="cand_003",
                    status="filled",
                    mode="live",
                    payload={"symbol": "SOLUSDT"},
                    created_at=now - timedelta(days=3),
                    updated_at=now - timedelta(days=3),
                ),
                ExecutionModel(
                    execution_id="exe_004",
                    idempotency_key="idem_004",
                    candidate_id="cand_001",
                    status="expired",
                    mode="paper",
                    payload={"symbol": "BTCUSDT", "setup_type": "breakout_retest"},
                    created_at=now - timedelta(hours=4),
                    updated_at=now - timedelta(hours=2),
                ),
            ]
        )
        db.add_all(
            [
                PositionModel(
                    position_id="pos_001",
                    execution_id="exe_001",
                    candidate_id="cand_001",
                    signal_id="sig_001",
                    symbol="BTCUSDT",
                    side="long",
                    status=PositionStatus.OPEN.value,
                    quantity=1.0,
                    entry_price=100.0,
                    stop_loss=95.0,
                    take_profit=[110.0],
                    opened_at=now - timedelta(hours=1),
                    closed_at=None,
                    close_price=None,
                    close_reason=None,
                    ttl_expires_at=now + timedelta(hours=3),
                    created_at=now - timedelta(hours=1),
                    updated_at=now - timedelta(minutes=10),
                ),
                PositionModel(
                    position_id="pos_002",
                    execution_id="exe_002",
                    candidate_id="cand_002",
                    signal_id="sig_002",
                    symbol="ETHUSDT",
                    side="short",
                    status=PositionStatus.CLOSED.value,
                    quantity=2.0,
                    entry_price=200.0,
                    stop_loss=210.0,
                    take_profit=[180.0],
                    opened_at=now - timedelta(days=2),
                    closed_at=now - timedelta(days=1),
                    close_price=190.0,
                    close_reason="take_profit",
                    ttl_expires_at=None,
                    created_at=now - timedelta(days=2),
                    updated_at=now - timedelta(days=1),
                ),
                PositionModel(
                    position_id="pos_003",
                    execution_id="exe_003",
                    candidate_id="cand_003",
                    signal_id="sig_003",
                    symbol="SOLUSDT",
                    side="long",
                    status=PositionStatus.CLOSED.value,
                    quantity=1.0,
                    entry_price=50.0,
                    stop_loss=45.0,
                    take_profit=[60.0],
                    opened_at=now - timedelta(days=3),
                    closed_at=now - timedelta(days=2),
                    close_price=60.0,
                    close_reason="take_profit",
                    ttl_expires_at=None,
                    created_at=now - timedelta(days=3),
                    updated_at=now - timedelta(days=2),
                ),
                PositionModel(
                    position_id="pos_004",
                    execution_id="exe_004",
                    candidate_id="cand_001",
                    signal_id="sig_001",
                    symbol="BTCUSDT",
                    side="long",
                    status=PositionStatus.EXPIRED.value,
                    quantity=1.0,
                    entry_price=100.0,
                    stop_loss=95.0,
                    take_profit=[110.0],
                    opened_at=now - timedelta(hours=4),
                    closed_at=now - timedelta(hours=2),
                    close_price=100.0,
                    close_reason="expired",
                    ttl_expires_at=now - timedelta(hours=2),
                    created_at=now - timedelta(hours=4),
                    updated_at=now - timedelta(hours=2),
                ),
            ]
        )
        db.add_all(
            [
                IncidentModel(
                    incident_id="inc_001",
                    incident_type="execution_failed",
                    severity="warning",
                    source_service="execution-service",
                    message="execution warning",
                    correlation_id="corr_001",
                    payload={"execution_id": "exe_001"},
                    created_at=now - timedelta(hours=2),
                ),
                IncidentModel(
                    incident_id="inc_002",
                    incident_type="degraded_mode",
                    severity="error",
                    source_service="orchestrator",
                    message="older incident",
                    correlation_id="corr_002",
                    payload={},
                    created_at=now - timedelta(days=2),
                ),
            ]
        )
        db.add_all(
            [
                JournalEventModel(
                    event_id="evt_001",
                    event_type="candidate_created",
                    severity="info",
                    correlation_id="corr_001",
                    payload={"candidate_id": "cand_001"},
                    created_at=now - timedelta(hours=3),
                ),
                JournalEventModel(
                    event_id="evt_002",
                    event_type="candidate_rejected",
                    severity="warning",
                    correlation_id="corr_002",
                    payload={"candidate_id": "cand_003"},
                    created_at=now - timedelta(days=3),
                ),
            ]
        )
        db.commit()


def test_dashboard_summary_returns_correct_structure():
    client, session_factory = make_client()
    try:
        seed_dashboard_rows(session_factory)

        response = client.get("/v1/dashboard/summary")

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["service"] == "dashboard-service"
        data = body["data"]
        assert "kill_switch_active" in data
        assert data["kill_switch_active"] is False
        assert isinstance(data["pending_candidates_count"], int)
        assert isinstance(data["open_positions_count"], int)
        assert isinstance(data["recent_incidents_count"], int)
        assert isinstance(data["recent_journal_events_count"], int)
        assert data["pending_candidates_count"] == 1
        assert data["open_positions_count"] == 1
        assert data["recent_incidents_count"] == 1
        assert data["recent_journal_events_count"] == 1
    finally:
        teardown_client(client)


def test_dashboard_candidates_returns_list():
    client, session_factory = make_client()
    try:
        seed_dashboard_rows(session_factory)

        response = client.get("/v1/dashboard/candidates")

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 2
        item = body["data"][0]
        assert "candidate_id" in item
        assert "status" in item
        assert "symbol" in item
    finally:
        teardown_client(client)


def test_dashboard_positions_returns_list():
    client, session_factory = make_client()
    try:
        seed_dashboard_rows(session_factory)

        response = client.get("/v1/dashboard/positions")

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 1
        item = body["data"][0]
        assert "position_id" in item
        assert "symbol" in item
        assert "status" in item
        assert item["position_id"] == "pos_001"
    finally:
        teardown_client(client)


def test_dashboard_incidents_returns_list():
    client, session_factory = make_client()
    try:
        seed_dashboard_rows(session_factory)

        response = client.get("/v1/dashboard/incidents")

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 2
        item = body["data"][0]
        assert "incident_id" in item
        assert "severity" in item
    finally:
        teardown_client(client)


def test_dashboard_stats_returns_aggregated_metrics():
    client, session_factory = make_client()
    try:
        seed_dashboard_rows(session_factory)

        response = client.get("/v1/dashboard/stats")

        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["total_trades"] == 2
        assert data["win_rate_pct"] == 50.0
        assert data["avg_rr"] == 0.5
        assert data["total_pnl_usdt"] == 20.0
        assert data["avg_hold_candles"] == 0.0
        assert data["by_symbol"]["ETHUSDT"]["total_trades"] == 1
        assert data["by_symbol"]["ETHUSDT"]["total_pnl_usdt"] == 20.0
        assert data["by_symbol"]["BTCUSDT"]["total_trades"] == 1
        assert data["by_symbol"]["BTCUSDT"]["total_pnl_usdt"] == 0.0
        assert data["by_setup_type"]["trend_continuation"]["total_trades"] == 1
        assert data["by_setup_type"]["trend_continuation"]["avg_rr"] == 1.0
        assert data["by_setup_type"]["breakout_retest"]["total_trades"] == 1
        assert "SOLUSDT" not in data["by_symbol"]
    finally:
        teardown_client(client)
