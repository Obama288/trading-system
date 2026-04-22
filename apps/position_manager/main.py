from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from apps.position_manager.application.close_position import close_position_use_case
from apps.position_manager.application.open_position import open_position_use_case
from apps.position_manager.application.reconcile import reconcile_positions_use_case
from apps.position_manager.config import get_config
from apps.position_manager.infrastructure.journal_client import HttpAlertClient, HttpJournalClient, NoopAlertClient
from apps.position_manager.infrastructure.position_repo import PositionRepository
from apps.position_manager.schemas.requests import PositionCloseRequest, PositionOpenRequest, ReconcileRequest
from libs.db.session import get_db
from libs.logging.context import get_correlation_id, set_correlation_id
from libs.schemas.common import ServiceEnvelope

app = FastAPI(title="position-manager")
CONFIG = get_config()
JOURNAL_CLIENT = HttpJournalClient(base_url=CONFIG.journal_service_base_url)
ALERT_CLIENT = (
    HttpAlertClient(base_url=CONFIG.alerts_service_base_url)
    if CONFIG.alerts_enabled
    else NoopAlertClient()
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    response = await call_next(request)
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
def open_position(req: PositionOpenRequest, db: Session = Depends(get_db)) -> ServiceEnvelope[dict]:
    repo = PositionRepository(db)
    result = open_position_use_case(
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
def close_position(req: PositionCloseRequest, db: Session = Depends(get_db)) -> ServiceEnvelope[dict]:
    repo = PositionRepository(db)
    result = close_position_use_case(
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
def reconcile_positions(req: ReconcileRequest, db: Session = Depends(get_db)) -> ServiceEnvelope[dict]:
    repo = PositionRepository(db)
    result = reconcile_positions_use_case(
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


@app.get("/v1/positions/open")
def list_open_positions(request: Request, db: Session = Depends(get_db)) -> ServiceEnvelope[list[dict]]:
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
