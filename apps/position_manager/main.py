from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from apps.position_manager.application.close_position import close_position_use_case
from apps.position_manager.application.open_position import open_position_use_case
from apps.position_manager.application.reconcile import reconcile_positions_use_case
from apps.position_manager.application.reconcile_scheduler import run_reconcile_scheduler_loop
from apps.position_manager.application.recover_position import recover_position_use_case
from apps.position_manager.config import get_config
from apps.position_manager.infrastructure.journal_client import HttpAlertClient, HttpJournalClient, NoopAlertClient
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionCloseRequest, PositionOpenRequest, PositionRecoverRequest, ReconcileRequest
from libs.db.session import get_db, get_session_factory
from libs.db.startup_health import ensure_db_connection_startup
from libs.logging.context import get_correlation_id, set_correlation_id
from libs.schemas.common import ServiceEnvelope
from libs.clients.okx_market_data_fetcher import OkxMarketDataFetcher
from libs.security import require_internal_service_auth, require_operator_auth, validate_startup_auth

CONFIG = get_config()
LOGGER = logging.getLogger(__name__)
JOURNAL_CLIENT = HttpJournalClient(base_url=CONFIG.journal_service_base_url)
ALERT_CLIENT = (
    HttpAlertClient(base_url=CONFIG.alerts_service_base_url)
    if CONFIG.alerts_enabled
    else NoopAlertClient()
)
RECONCILE_TASK: asyncio.Task | None = None
RECONCILE_STOP: asyncio.Event | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global RECONCILE_TASK, RECONCILE_STOP
    validate_startup_auth(require_internal=True, require_operator=True)
    await ensure_db_connection_startup(service_name=CONFIG.service_name, app=app)
    if CONFIG.reconcile_scheduler_enabled and CONFIG.execution_mode == "paper":
        RECONCILE_STOP = asyncio.Event()
        RECONCILE_TASK = asyncio.create_task(
            run_reconcile_scheduler_loop(
                session_factory=get_session_factory(),
                journal_client=JOURNAL_CLIENT,
                alert_client=ALERT_CLIENT,
                market_fetcher=OkxMarketDataFetcher(),
                interval_seconds=CONFIG.reconcile_scheduler_interval_seconds,
                timeframe=CONFIG.reconcile_scheduler_timeframe,
                candle_limit=CONFIG.reconcile_scheduler_candle_limit,
                continue_on_error=CONFIG.reconcile_scheduler_continue_on_error,
                stop_event=RECONCILE_STOP,
            ),
            name="position_reconcile_scheduler",
        )
        LOGGER.info(
            "position reconcile scheduler started",
            extra={
                "interval_seconds": CONFIG.reconcile_scheduler_interval_seconds,
                "timeframe": CONFIG.reconcile_scheduler_timeframe,
                "candle_limit": CONFIG.reconcile_scheduler_candle_limit,
                "continue_on_error": CONFIG.reconcile_scheduler_continue_on_error,
            },
        )
    yield
    if RECONCILE_STOP is not None:
        RECONCILE_STOP.set()
    if RECONCILE_TASK is not None:
        await RECONCILE_TASK


app = FastAPI(title="position-manager", lifespan=lifespan)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    try:
        response = await call_next(request)
    except Exception:
        LOGGER.exception("unhandled_exception_in_middleware", extra={"correlation_id": corr})
        response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
    response.headers["X-Correlation-Id"] = corr
    return response


@app.get("/health")
def health(request: Request) -> ServiceEnvelope[dict]:
    correlation_id = request.headers.get("X-Correlation-Id") or get_correlation_id()
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=correlation_id,
        data={"status": "healthy"},
        error=None,
    )


@app.post("/v1/positions/open")
async def open_position(
    req: PositionOpenRequest,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> ServiceEnvelope[dict]:
    repo = PositionRepository(db)
    result = await open_position_use_case(
        repo=repo,
        journal_client=JOURNAL_CLIENT,
        alert_client=ALERT_CLIENT,
        req=req,
    )
    return ServiceEnvelope[dict](
        ok=result["ok"],
        service=CONFIG.service_name,
        correlation_id=req.correlation_id,
        data=result if result["ok"] else None,
        error=None if result["ok"] else {"code": result["code"]},
    )


@app.post("/v1/positions/close")
async def close_position(
    req: PositionCloseRequest,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> ServiceEnvelope[dict]:
    repo = PositionRepository(db)
    result = await close_position_use_case(
        repo=repo,
        journal_client=JOURNAL_CLIENT,
        alert_client=ALERT_CLIENT,
        req=req,
    )
    return ServiceEnvelope[dict](
        ok=result["ok"],
        service=CONFIG.service_name,
        correlation_id=req.correlation_id,
        data=result if result["ok"] else None,
        error=None if result["ok"] else {"code": result["code"]},
    )


@app.post("/v1/positions/reconcile")
async def reconcile_positions(
    req: ReconcileRequest,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> ServiceEnvelope[dict]:
    repo = PositionRepository(db)
    result = await reconcile_positions_use_case(
        repo=repo,
        journal_client=JOURNAL_CLIENT,
        alert_client=ALERT_CLIENT,
        req=req,
    )
    return ServiceEnvelope[dict](
        ok=result["ok"],
        service=CONFIG.service_name,
        correlation_id=req.correlation_id,
        data=result,
        error=None,
    )


@app.post("/v1/positions/recover")
async def recover_position(
    req: PositionRecoverRequest,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> ServiceEnvelope[dict]:
    repo = PositionRepository(db)
    result = await recover_position_use_case(
        repo=repo,
        journal_client=JOURNAL_CLIENT,
        alert_client=ALERT_CLIENT,
        execution_id=req.execution_id,
        correlation_id=req.correlation_id,
    )
    return ServiceEnvelope[dict](
        ok=result["ok"],
        service=CONFIG.service_name,
        correlation_id=req.correlation_id,
        data=result if result["ok"] else None,
        error=None if result["ok"] else {"code": result["code"]},
    )


@app.get("/v1/positions/open")
def list_open_positions(
    request: Request,
    _: str = require_operator_auth(),
    db: Session = Depends(get_db),
) -> ServiceEnvelope[list[dict]]:
    correlation_id = request.headers.get("X-Correlation-Id") or get_correlation_id()
    repo = PositionRepository(db)
    items = [repo.to_dict(model) for model in repo.list_open_positions()]
    return ServiceEnvelope[list[dict]](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=correlation_id,
        data=items,
        error=None,
    )
