from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from apps.incidents.application.list_incidents import list_incidents_use_case
from apps.incidents.application.record_incident import record_incident_use_case
from apps.incidents.config import get_config
from apps.incidents.infrastructure.incident_repo import IncidentRepository
from apps.incidents.infrastructure.journal_client import HttpJournalClient
from apps.incidents.schemas.requests import ListIncidentsRequest, RecordIncidentRequest
from libs.db.session import get_db
from libs.db.startup_health import ensure_db_connection_startup
from libs.logging.context import get_correlation_id, set_correlation_id
from libs.schemas.common import ServiceEnvelope
from libs.security import require_internal_service_auth, require_operator_auth, validate_startup_auth

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup_auth(require_internal=True, require_operator=True)
    config = get_config()
    await ensure_db_connection_startup(service_name=config.service_name, app=app)
    yield


CONFIG = get_config()
JOURNAL_CLIENT = HttpJournalClient(base_url=CONFIG.journal_service_base_url)

app = FastAPI(title="incidents", lifespan=lifespan)


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
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=request.headers.get("X-Correlation-Id") or get_correlation_id(),
        data={"status": "healthy"},
        error=None,
    )


@app.post("/v1/incidents/record")
async def record_incident(
    req: RecordIncidentRequest,
    db: Session = Depends(get_db),
    _: str = require_internal_service_auth(),
) -> ServiceEnvelope[dict]:
    repo = IncidentRepository(db)
    result = await record_incident_use_case(
        repo=repo,
        journal_client=JOURNAL_CLIENT,
        req=req,
    )
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=req.correlation_id,
        data=result,
        error=None,
    )


@app.get("/v1/incidents")
def list_incidents(
    request: Request,
    _: str = require_operator_auth(),
    incident_type: str | None = None,
    severity: str | None = None,
    source_service: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> ServiceEnvelope[dict]:
    repo = IncidentRepository(db)
    req = ListIncidentsRequest(
        incident_type=incident_type,
        severity=severity,
        source_service=source_service,
        limit=limit,
        offset=offset,
    )
    result = list_incidents_use_case(repo=repo, req=req)
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=request.headers.get("X-Correlation-Id") or get_correlation_id(),
        data=result,
        error=None,
    )


@app.get("/v1/incidents/{incident_id}")
def get_incident(
    incident_id: str,
    request: Request,
    _: str = require_operator_auth(),
    db: Session = Depends(get_db),
) -> ServiceEnvelope[dict]:
    repo = IncidentRepository(db)
    row = repo.get_incident(incident_id)
    if row is None:
        return ServiceEnvelope[dict](
            ok=False,
            service=CONFIG.service_name,
            correlation_id=request.headers.get("X-Correlation-Id") or get_correlation_id(),
            data=None,
            error={"code": "NOT_FOUND"},
        )
    return ServiceEnvelope[dict](
        ok=True,
        service=CONFIG.service_name,
        correlation_id=request.headers.get("X-Correlation-Id") or get_correlation_id(),
        data=repo.to_dict(row),
        error=None,
    )
