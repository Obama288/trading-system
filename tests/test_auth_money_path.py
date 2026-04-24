"""
Integration tests: auth chain on the money-path.

Verifies that each service enforces its auth tier correctly:
  - orchestrator /approve      -> require_operator_auth  (X-Operator-Token)
  - execution_service /place   -> require_internal_service_auth (X-Internal-Token)
  - kill_switch /halt          -> require_admin_auth     (X-Admin-Token)

Token taxonomy:
  - _INTERNAL_TOKEN : correct INTERNAL_SERVICE_TOKEN value
  - _OPERATOR_TOKEN : correct OPERATOR_TOKEN value
  - _ADMIN_TOKEN    : correct ADMIN_TOKEN value
  - _WRONG_TOKEN    : a valid-format token that is wrong for every tier

IMPORTANT: INTERNAL_SERVICE_TOKEN must be set before the orchestrator and
execution_service app modules are imported, because both instantiate
HttpKillSwitchClient / HttpExecutionClient at module level.
"""
from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ──────────────────────────────────────────────────────────────────────────────
# Token constants
# ──────────────────────────────────────────────────────────────────────────────
_INTERNAL_TOKEN = "test-int-tok-money-path-auth-0000001"
_OPERATOR_TOKEN = "test-op-tok-money-path-auth-00000001"
_ADMIN_TOKEN    = "test-admin-tok-money-path-auth-000001"
_WRONG_TOKEN    = "wrong-tok-money-path-auth-000000001"

# Must be set before importing app modules that create module-level HTTP clients.
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", _INTERNAL_TOKEN)
os.environ.setdefault("OPERATOR_TOKEN", _OPERATOR_TOKEN)
os.environ.setdefault("ADMIN_TOKEN", _ADMIN_TOKEN)

# ── app imports (after env setup) ────────────────────────────────────────────
from apps.execution_service.main import app as execution_app  # noqa: E402
from apps.kill_switch.main import app as kill_switch_app       # noqa: E402
from apps.orchestrator.main import app as orchestrator_app     # noqa: E402
from libs.db.base import Base                                  # noqa: E402
from libs.db.session import get_db                             # noqa: E402


# ──────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────────────────────────
def _sqlite_session_factory() -> sessionmaker:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _db_override(sf: sessionmaker):
    def _inner() -> Generator[Session, None, None]:
        db = sf()
        try:
            yield db
        finally:
            db.close()
    return _inner


# ──────────────────────────────────────────────────────────────────────────────
# Request bodies
# ──────────────────────────────────────────────────────────────────────────────
_APPROVE_BODY = {
    "candidate_id": "cand_auth_test_nonexistent",
    "telegram_user_id": 1,
    "correlation_id": "corr_auth_approve",
}

_PLACE_BODY = {
    "candidate_id": "cand_auth_test",
    "execution_candidate": {
        "symbol": "BTCUSDT",
        "side": "buy",
        "order_type": "limit",
        "entry_price": 100.0,
        "quantity": 1.0,
        "stop_loss": 95.0,
        "take_profit": [110.0],
        "time_in_force": "GTC",
    },
    "execution_idempotency_key": "idem_auth_test_0001",
    "correlation_id": "corr_auth_place",
}

_HALT_BODY = {
    "operator_user_id": 99,
    "reason": "auth_test_halt",
    "actor": "auth-tester",
    "correlation_id": "corr_auth_halt",
}


# ──────────────────────────────────────────────────────────────────────────────
# Scenarios 1–3: operator auth on orchestrator /v1/pipeline/approve
# ──────────────────────────────────────────────────────────────────────────────
class TestApproveOperatorAuth:
    """
    /approve is protected by require_operator_auth (X-Operator-Token).
    A non-existent candidate_id returns NOT_FOUND (200) before the use case
    reaches kill_switch or execution_client, so no downstream mocking is needed.
    """

    def _client(self) -> TestClient:
        os.environ["OPERATOR_TOKEN"] = _OPERATOR_TOKEN
        orchestrator_app.dependency_overrides[get_db] = _db_override(_sqlite_session_factory())
        return TestClient(orchestrator_app)

    def _teardown(self, client: TestClient) -> None:
        client.close()
        orchestrator_app.dependency_overrides.pop(get_db, None)
        os.environ.pop("OPERATOR_TOKEN", None)

    def test_valid_operator_token_reaches_handler(self):
        """Scenario 1: correct token — auth passes, business logic runs (NOT_FOUND, not 401/403)."""
        client = self._client()
        try:
            response = client.post(
                "/v1/pipeline/approve",
                json=_APPROVE_BODY,
                headers={"X-Operator-Token": _OPERATOR_TOKEN},
            )
            assert response.status_code not in {401, 403}
            # Specifically: NOT_FOUND because the candidate doesn't exist
            assert response.json().get("code") == "NOT_FOUND"
        finally:
            self._teardown(client)

    def test_missing_operator_token_returns_401(self):
        """Scenario 2: no token header — middleware returns 401."""
        client = self._client()
        try:
            response = client.post("/v1/pipeline/approve", json=_APPROVE_BODY)
            assert response.status_code == 401
        finally:
            self._teardown(client)

    def test_wrong_operator_token_returns_403(self):
        """Scenario 3: token present but wrong value — middleware returns 403."""
        client = self._client()
        try:
            response = client.post(
                "/v1/pipeline/approve",
                json=_APPROVE_BODY,
                headers={"X-Operator-Token": _WRONG_TOKEN},
            )
            assert response.status_code == 403
        finally:
            self._teardown(client)


# ──────────────────────────────────────────────────────────────────────────────
# Scenarios 4–5: internal service auth on execution_service /v1/execution/place
# ──────────────────────────────────────────────────────────────────────────────
class TestPlaceExecutionInternalAuth:
    """
    /place is protected by require_internal_service_auth (X-Internal-Token).
    place_order_use_case is patched so the test stays auth-focused and does
    not depend on config files, kill_switch availability, or position_manager.
    """

    def _client(self) -> TestClient:
        os.environ["INTERNAL_SERVICE_TOKEN"] = _INTERNAL_TOKEN
        execution_app.dependency_overrides[get_db] = _db_override(_sqlite_session_factory())
        return TestClient(execution_app)

    def _teardown(self, client: TestClient) -> None:
        client.close()
        execution_app.dependency_overrides.pop(get_db, None)

    def test_valid_internal_token_reaches_handler(self):
        """Scenario 4: correct token — auth passes, use case called (not 401/403)."""
        client = self._client()
        try:
            with patch(
                "apps.execution_service.main.place_order_use_case",
                new=AsyncMock(return_value={
                    "accepted": False,
                    "duplicate": False,
                    "execution_id": None,
                    "candidate_id": "cand_auth_test",
                    "status": "blocked",
                    "mode": "paper",
                    "payload": None,
                    "error": {"code": "KILL_SWITCH_ACTIVE"},
                }),
            ):
                response = client.post(
                    "/v1/execution/place",
                    json=_PLACE_BODY,
                    headers={"X-Internal-Token": _INTERNAL_TOKEN},
                )
            assert response.status_code not in {401, 403}
            assert response.json()["ok"] is False  # use-case result passed through
        finally:
            self._teardown(client)

    def test_missing_internal_token_returns_401(self):
        """Scenario 5: no token header — middleware returns 401."""
        client = self._client()
        try:
            response = client.post("/v1/execution/place", json=_PLACE_BODY)
            assert response.status_code == 401
        finally:
            self._teardown(client)


# ──────────────────────────────────────────────────────────────────────────────
# Scenarios 6–8: admin auth on kill_switch /v1/kill-switch/halt
# ──────────────────────────────────────────────────────────────────────────────
class TestHaltAdminAuth:
    """
    /halt is protected by require_admin_auth (X-Admin-Token).
    The SQLite override makes the full handler execute successfully for the
    valid-token case so we can assert a 200 OK with state changes.
    """

    def _client(self) -> TestClient:
        os.environ["ADMIN_TOKEN"] = _ADMIN_TOKEN
        kill_switch_app.dependency_overrides[get_db] = _db_override(_sqlite_session_factory())
        return TestClient(kill_switch_app)

    def _teardown(self, client: TestClient) -> None:
        client.close()
        kill_switch_app.dependency_overrides.pop(get_db, None)
        os.environ.pop("ADMIN_TOKEN", None)

    def test_valid_admin_token_halts_successfully(self):
        """Scenario 6: correct token — halt completes, 200 OK, kill switch active."""
        client = self._client()
        try:
            response = client.post(
                "/v1/kill-switch/halt",
                json=_HALT_BODY,
                headers={"X-Admin-Token": _ADMIN_TOKEN},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["ok"] is True
            assert body["data"]["kill_switch_active"] is True
            assert body["data"]["trading_enabled"] is False
        finally:
            self._teardown(client)

    def test_missing_admin_token_returns_401(self):
        """Scenario 7: no token header — middleware returns 401."""
        client = self._client()
        try:
            response = client.post("/v1/kill-switch/halt", json=_HALT_BODY)
            assert response.status_code == 401
        finally:
            self._teardown(client)

    def test_wrong_admin_token_returns_403(self):
        """Scenario 8: token present but wrong value — middleware returns 403."""
        client = self._client()
        try:
            response = client.post(
                "/v1/kill-switch/halt",
                json=_HALT_BODY,
                headers={"X-Admin-Token": _WRONG_TOKEN},
            )
            assert response.status_code == 403
        finally:
            self._teardown(client)
