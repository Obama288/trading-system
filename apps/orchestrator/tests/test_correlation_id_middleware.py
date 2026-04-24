from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from libs.logging.context import set_correlation_id


def _make_app() -> FastAPI:
    """Minimal app reproducing the middleware pattern used in all services."""
    test_app = FastAPI()

    @test_app.middleware("http")
    async def correlation_id_middleware(request, call_next):
        corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
        set_correlation_id(corr)
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
        response.headers["X-Correlation-Id"] = corr
        return response

    @test_app.get("/ok")
    def ok_route():
        return {"ok": True}

    @test_app.get("/explode")
    def explode_route():
        raise RuntimeError("boom")

    return test_app


def test_correlation_id_echoed_on_success():
    client = TestClient(_make_app(), raise_server_exceptions=False)
    response = client.get("/ok", headers={"X-Correlation-Id": "trace-001"})
    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"] == "trace-001"


def test_correlation_id_generated_when_absent():
    client = TestClient(_make_app(), raise_server_exceptions=False)
    response = client.get("/ok")
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id", "").startswith("corr_")


def test_correlation_id_present_on_unhandled_exception():
    """X-Correlation-Id must be set even when the route raises an unhandled exception."""
    client = TestClient(_make_app(), raise_server_exceptions=False)
    response = client.get("/explode", headers={"X-Correlation-Id": "trace-500"})
    assert response.status_code == 500
    assert response.headers["X-Correlation-Id"] == "trace-500"


def test_correlation_id_generated_on_unhandled_exception_without_header():
    client = TestClient(_make_app(), raise_server_exceptions=False)
    response = client.get("/explode")
    assert response.status_code == 500
    assert response.headers.get("X-Correlation-Id", "").startswith("corr_")
