from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from apps.incidents.application.list_incidents import list_incidents_use_case
from apps.incidents.application.record_incident import record_incident_use_case
from apps.incidents.config import get_config
from apps.incidents.infrastructure.incident_repo import IncidentRepository
from apps.incidents.infrastructure.journal_client import HttpJournalClient
from apps.incidents.schemas.requests import ListIncidentsRequest, RecordIncidentRequest
from libs.db.session import get_db
from libs.logging.context import get_correlation_id, set_correlation_id
from libs.schemas.common import ServiceEnvelope

app = FastAPI(title="incidents")
CONFIG = get_config()
JOURNAL_CLIENT = HttpJournalClient(base_url=CONFIG.journal_service_base_url)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr = request.headers.get("X-Correlation-Id") or f"corr_{uuid4().hex}"
    set_correlation_id(corr)
    response = await call_next(request)
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
def record_incident(req: RecordIncidentRequest, db: Session = Depends(get_db)) -> ServiceEnvelope[dict]:
    repo = IncidentRepository(db)
    result = record_incident_use_case(
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
def get_incident(incident_id: str, request: Request, db: Session = Depends(get_db)) -> ServiceEnvelope[dict]:
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
