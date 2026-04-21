from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from apps.execution_service.application.cancel_order_dry_run import cancel_order_dry_run_use_case
from apps.execution_service.application.place_order_dry_run import place_order_dry_run_use_case
from apps.execution_service.infrastructure.execution_store import InMemoryExecutionStore
from apps.execution_service.infrastructure.kill_switch_client import HttpKillSwitchClient
from apps.execution_service.schemas.requests import CancelExecutionRequest, PlaceExecutionRequest
from libs.logging.context import set_correlation_id

app = FastAPI(title="execution-service")

STORE = InMemoryExecutionStore()
KILL_SWITCH = HttpKillSwitchClient(base_url=os.getenv("KILL_SWITCH_BASE_URL", "http://kill-switch:8000"))
APP_VERSION = "v1"


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr
    return response


@app.get("/health")
def health() -> dict:
    return {"service": "execution-service", "status": "healthy"}


@app.get("/ready")
def ready() -> dict:
    return {"service": "execution-service", "status": "ready", "mode": "dry_run"}


@app.get("/metrics")
def metrics() -> dict:
    # MVP placeholder. Replace with Prometheus/text exposition later.
    return {"service": "execution-service", "mode": "dry_run", "metrics": {}}


@app.get("/version")
def version() -> dict:
    return {"service": "execution-service", "version": APP_VERSION, "mode": "dry_run"}


@app.post("/v1/execution/place")
def place_execution(req: PlaceExecutionRequest) -> dict:
    try:
        result = place_order_dry_run_use_case(
            candidate_id=req.candidate_id,
            execution_candidate=req.execution_candidate,
            execution_idempotency_key=req.execution_idempotency_key,
            correlation_id=req.correlation_id,
            kill_switch_client=KILL_SWITCH,
            store=STORE,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "ok": result["accepted"],
        "service": "execution-service",
        "version": APP_VERSION,
        "correlation_id": req.correlation_id,
        "data": result,
        "error": result.get("error"),
    }


@app.post("/v1/execution/cancel")
def cancel_execution(req: CancelExecutionRequest) -> dict:
    result = cancel_order_dry_run_use_case(
        execution_id=req.execution_id,
        store=STORE,
    )
    return {
        "ok": result["ok"],
        "service": "execution-service",
        "version": APP_VERSION,
        "correlation_id": req.correlation_id,
        "data": result,
        "error": None if result["ok"] else {"code": "NOT_FOUND"},
    }
