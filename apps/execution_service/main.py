from __future__ import annotations

import os
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from apps.execution_service.application.cancel_order_dry_run import cancel_order_dry_run_use_case
from apps.execution_service.application.place_order import place_order_use_case
from apps.execution_service.infrastructure.execution_store_db import DbExecutionStore
from apps.execution_service.infrastructure.local_clients import DbJournalClient, NoopAlertClient
from apps.execution_service.schemas.requests import CancelExecutionRequest, PlaceExecutionRequest
from apps.position_manager.infrastructure.position_repo import PositionRepository
from libs.clients.kill_switch_client import HttpKillSwitchClient
from libs.db.session import get_db
from libs.logging.context import set_correlation_id

app = FastAPI(title="execution-service")

KILL_SWITCH = HttpKillSwitchClient(base_url=os.getenv("KILL_SWITCH_BASE_URL", "http://kill-switch:8000"))
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "paper").lower()
APP_VERSION = "v1"


@app.on_event("startup")
async def startup_validate_execution_mode() -> None:
    print(f"[execution-service] EXECUTION_MODE={EXECUTION_MODE}", flush=True)
    if EXECUTION_MODE not in {"paper", "dry_run"}:
        raise RuntimeError(f"Unsafe EXECUTION_MODE: {EXECUTION_MODE}")


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
    return {"service": "execution-service", "status": "ready", "mode": EXECUTION_MODE}


@app.get("/metrics")
def metrics() -> dict:
    # MVP placeholder. Replace with Prometheus/text exposition later.
    return {"service": "execution-service", "mode": EXECUTION_MODE, "metrics": {}}


@app.get("/version")
def version() -> dict:
    return {"service": "execution-service", "version": APP_VERSION, "mode": EXECUTION_MODE}


@app.post("/v1/execution/place")
async def place_execution(req: PlaceExecutionRequest, db: Session = Depends(get_db)) -> dict:
    store = DbExecutionStore(db)
    position_repo = PositionRepository(db)
    journal_client = DbJournalClient(db)
    alert_client = NoopAlertClient()
    try:
        result = await place_order_use_case(
            candidate_id=req.candidate_id,
            execution_candidate=req.execution_candidate,
            execution_idempotency_key=req.execution_idempotency_key,
            correlation_id=req.correlation_id,
            kill_switch_client=KILL_SWITCH,
            store=store,
            position_repo=position_repo,
            journal_client=journal_client,
            alert_client=alert_client,
            execution_mode=EXECUTION_MODE,
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
def cancel_execution(req: CancelExecutionRequest, db: Session = Depends(get_db)) -> dict:
    store = DbExecutionStore(db)
    result = cancel_order_dry_run_use_case(
        execution_id=req.execution_id,
        store=store,
    )
    return {
        "ok": result["ok"],
        "service": "execution-service",
        "version": APP_VERSION,
        "correlation_id": req.correlation_id,
        "data": result,
        "error": None if result["ok"] else {"code": "NOT_FOUND"},
    }
