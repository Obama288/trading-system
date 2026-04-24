from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from apps.execution_service.application.cancel_order_dry_run import cancel_order_dry_run_use_case
from apps.execution_service.application.detect_orphans import detect_orphan_executions_use_case_async
from apps.execution_service.application.orphan_scheduler import run_orphan_scheduler_loop
from apps.execution_service.application.place_order import place_order_use_case
from apps.execution_service.infrastructure.position_admission_repo import DbPositionAdmissionRepo
from apps.execution_service.infrastructure.position_manager_client import HttpPositionManagerClient
from apps.execution_service.infrastructure.execution_store_db import DbExecutionStore
from apps.execution_service.infrastructure.local_clients import DbJournalClient, NoopAlertClient
from apps.execution_service.schemas.requests import CancelExecutionRequest, PlaceExecutionRequest
from libs.clients.kill_switch_client import HttpKillSwitchClient
from libs.db.session import get_db, get_session_factory
from libs.db.startup_health import ensure_db_connection_startup
from libs.logging.context import set_correlation_id
from libs.security import require_internal_service_auth, validate_startup_auth

LOGGER = logging.getLogger(__name__)


EXECUTION_MODE = os.getenv("EXECUTION_MODE", "paper").lower()

ORPHAN_TASK: asyncio.Task | None = None
ORPHAN_STOP: asyncio.Event | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ORPHAN_TASK, ORPHAN_STOP
    print(f"[execution-service] EXECUTION_MODE={EXECUTION_MODE}", flush=True)
    if EXECUTION_MODE not in {"paper", "dry_run"}:
        raise RuntimeError(f"Unsafe EXECUTION_MODE: {EXECUTION_MODE}")
    validate_startup_auth(require_internal=True)
    await ensure_db_connection_startup(service_name="execution-service", app=app)
    ORPHAN_STOP = asyncio.Event()
    ORPHAN_TASK = asyncio.create_task(
        run_orphan_scheduler_loop(
            session_factory=get_session_factory(),
            interval_seconds=60.0,
            execution_mode=EXECUTION_MODE,
            continue_on_error=True,
            stop_event=ORPHAN_STOP,
        ),
        name="execution_orphan_scheduler",
    )
    LOGGER.info("orphan scheduler started", extra={"interval_seconds": 60})
    yield
    ORPHAN_STOP.set()
    if ORPHAN_TASK is not None:
        await ORPHAN_TASK


app = FastAPI(title="execution-service", lifespan=lifespan)

KILL_SWITCH = HttpKillSwitchClient(base_url=os.getenv("KILL_SWITCH_BASE_URL", "http://kill-switch:8000"))
APP_VERSION = "v1"


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    try:
        response = await call_next(request)
    except Exception:
        response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
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
async def place_execution(
    req: PlaceExecutionRequest,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> dict:
    store = DbExecutionStore(db)
    admission_repo = DbPositionAdmissionRepo(db)
    journal_client = DbJournalClient(db)
    alert_client = NoopAlertClient()
    position_manager_client = HttpPositionManagerClient(
        base_url=os.getenv("POSITION_MANAGER_BASE_URL", "http://position-manager:8000")
    )
    try:
        result = await place_order_use_case(
            candidate_id=req.candidate_id,
            execution_candidate=req.execution_candidate,
            execution_idempotency_key=req.execution_idempotency_key,
            correlation_id=req.correlation_id,
            kill_switch_client=KILL_SWITCH,
            store=store,
            admission_repo=admission_repo,
            position_manager_client=position_manager_client,
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
def cancel_execution(
    req: CancelExecutionRequest,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> dict:
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


@app.get("/v1/execution/orphans")
async def detect_orphans(
    request: Request,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
    mode: str | None = None,
    emit_events: bool = True,
) -> dict:
    correlation_id = request.headers.get("X-Correlation-ID") or "corr_orphan_detect"
    admission_repo = DbPositionAdmissionRepo(db)
    journal_client = DbJournalClient(db)

    def get_emitted_orphan_event_ids() -> set[str]:
        from libs.db.models.journal_event import JournalEventModel
        from sqlalchemy import select
        stmt = (
            select(JournalEventModel.event_id)
            .where(JournalEventModel.event_type == "orphan_execution_detected")
        )
        return set(db.execute(stmt).scalars().all())

    class DetectorAdapter:
        def get_pending_open_executions(self, mode: str | None = None) -> list:
            return admission_repo.get_pending_open_executions(mode=mode)

        def get_emitted_orphan_event_ids(self) -> set[str]:
            return get_emitted_orphan_event_ids()

        async def emit_detection_event(self, events: list[dict]) -> None:
            for evt in events:
                await journal_client.write(evt)

        async def emit_escalation_event(self, count: int) -> None:
            alert_client = NoopAlertClient()
            if count > 0:
                await alert_client.notify(
                    {
                        "event_type": "orphan_execution_detected",
                        "service": "execution-service",
                        "source": "orphan_detector",
                        "orphan_count": count,
                    }
                )

        def get_correlation_id(self) -> str:
            return correlation_id

        def get_journal_client(self):
            return journal_client

    result = await detect_orphan_executions_use_case_async(
        detector=DetectorAdapter(),
        mode=mode,
        emit_events=emit_events,
        correlation_id=correlation_id,
    )
    return {
        "ok": result["ok"],
        "service": "execution-service",
        "version": APP_VERSION,
        "correlation_id": correlation_id,
        "data": result,
        "error": None,
    }
