from __future__ import annotations

import os
from collections.abc import Generator
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-internal-token-risk-route-0001")

from apps.risk_engine import main as risk_main  # noqa: E402
from libs.db.base import Base  # noqa: E402
from libs.db.models.paper_account_authority import PaperAccountAuthorityModel  # noqa: E402
from libs.db.models.position import PositionModel  # noqa: E402
from libs.db.session import get_db  # noqa: E402

_TOKEN = "test-internal-token-risk-route-0001"


def _session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _override_get_db(sf: sessionmaker[Session]):
    def _inner() -> Generator[Session, None, None]:
        db = sf()
        try:
            yield db
        finally:
            db.close()

    return _inner


def _client(sf: sessionmaker[Session]) -> TestClient:
    risk_main.app.dependency_overrides[get_db] = _override_get_db(sf)
    return TestClient(risk_main.app)


def _teardown(client: TestClient) -> None:
    client.close()
    risk_main.app.dependency_overrides.pop(get_db, None)


def _risk_body(*, equity: float = 999999.0, daily_pnl: float = 0.0, open_positions: int = 999) -> dict:
    return {
        "signal_id": "sig_route_auth",
        "symbol": "BTCUSDT",
        "side": "long",
        "entry_zone": {"min": 100.0, "max": 102.0},
        "stop_loss": 95.0,
        "account_state": {
            "equity_usdt": equity,
            "daily_pnl_usdt": daily_pnl,
            "open_positions": open_positions,
            "portfolio_exposure_pct": 99.0,
        },
        "correlation_id": "corr_route_auth",
    }


def _seed_paper_equity(sf: sessionmaker[Session], *, equity: float = 1000.0) -> None:
    with sf() as db:
        db.add(
            PaperAccountAuthorityModel(
                account_key="default_paper_account",
                equity_usdt=equity,
                updated_by="test",
            )
        )
        db.commit()


def _seed_open_position(sf: sessionmaker[Session]) -> None:
    with sf() as db:
        db.add(
            PositionModel(
                position_id="pos_route_auth",
                execution_id="exec_route_auth",
                candidate_id="cand_route_auth",
                signal_id="sig_route_auth",
                symbol="BTCUSDT",
                side="long",
                status="open",
                quantity=1.0,
                entry_price=100.0,
                stop_loss=95.0,
                take_profit=[110.0],
                opened_at=datetime.now(timezone.utc),
            )
        )
        db.commit()


def test_protected_route_requires_internal_auth():
    sf = _session_factory()
    _seed_paper_equity(sf)
    client = _client(sf)
    try:
        response = client.post("/v1/risk/evaluate", json=_risk_body())

        assert response.status_code == 401
    finally:
        _teardown(client)


def test_protected_route_fails_closed_when_paper_equity_missing():
    sf = _session_factory()
    client = _client(sf)
    try:
        response = client.post(
            "/v1/risk/evaluate",
            json=_risk_body(equity=999999.0),
            headers={"X-Internal-Token": _TOKEN},
        )

        assert response.status_code == 503
        body = response.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "PAPER_EQUITY_AUTHORITY_MISSING"
    finally:
        _teardown(client)


def test_protected_route_fails_closed_when_paper_equity_unavailable(monkeypatch):
    sf = _session_factory()
    client = _client(sf)

    def _raise_unavailable(_db: Session) -> float:
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(risk_main, "_get_authoritative_equity_usdt", _raise_unavailable)
    try:
        response = client.post(
            "/v1/risk/evaluate",
            json=_risk_body(equity=999999.0),
            headers={"X-Internal-Token": _TOKEN},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "PAPER_EQUITY_AUTHORITY_UNAVAILABLE"
    finally:
        _teardown(client)


def test_protected_route_uses_service_side_equity_not_caller_equity():
    sf = _session_factory()
    _seed_paper_equity(sf, equity=1000.0)
    client = _client(sf)
    try:
        response = client.post(
            "/v1/risk/evaluate",
            json=_risk_body(equity=999999.0),
            headers={"X-Internal-Token": _TOKEN},
        )

        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "DAILY_PNL_AUTHORITY_UNAVAILABLE"
        assert body["data"]["approved"] is False
    finally:
        _teardown(client)


def test_protected_route_uses_service_side_open_positions_not_caller_count(monkeypatch):
    sf = _session_factory()
    _seed_paper_equity(sf, equity=1000.0)
    _seed_open_position(sf)
    observed: dict[str, int] = {}
    original = risk_main._get_authoritative_open_positions

    def _spy_open_positions(db: Session) -> int:
        count = original(db)
        observed["count"] = count
        return count

    monkeypatch.setattr(risk_main, "_get_authoritative_open_positions", _spy_open_positions)
    client = _client(sf)
    try:
        response = client.post(
            "/v1/risk/evaluate",
            json=_risk_body(open_positions=999),
            headers={"X-Internal-Token": _TOKEN},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DAILY_PNL_AUTHORITY_UNAVAILABLE"
        assert observed["count"] == 1
    finally:
        _teardown(client)


def test_protected_route_fails_closed_when_open_positions_unavailable(monkeypatch):
    sf = _session_factory()
    _seed_paper_equity(sf, equity=1000.0)

    def _raise_unavailable(_db: Session) -> int:
        raise RuntimeError("position db unavailable")

    monkeypatch.setattr(risk_main, "_get_authoritative_open_positions", _raise_unavailable)
    client = _client(sf)
    try:
        response = client.post(
            "/v1/risk/evaluate",
            json=_risk_body(open_positions=0),
            headers={"X-Internal-Token": _TOKEN},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "OPEN_POSITIONS_AUTHORITY_UNAVAILABLE"
    finally:
        _teardown(client)


def test_protected_route_fails_closed_because_a3_daily_pnl_authority_is_deferred():
    sf = _session_factory()
    _seed_paper_equity(sf, equity=1000.0)
    client = _client(sf)
    try:
        response = client.post(
            "/v1/risk/evaluate",
            json=_risk_body(daily_pnl=0.0),
            headers={"X-Internal-Token": _TOKEN},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DAILY_PNL_AUTHORITY_UNAVAILABLE"
    finally:
        _teardown(client)
