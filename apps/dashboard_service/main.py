from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from apps.dashboard_service.application.get_summary import get_dashboard_summary_use_case
from apps.dashboard_service.application.list_candidates import list_dashboard_candidates_use_case
from apps.dashboard_service.application.list_incidents import list_dashboard_incidents_use_case
from apps.dashboard_service.application.list_positions import list_dashboard_positions_use_case
from apps.dashboard_service.application.stats import get_dashboard_stats_use_case
from apps.dashboard_service.infrastructure.dashboard_repo import DashboardRepository
from apps.dashboard_service.infrastructure.stats_repo import StatsRepository
from apps.dashboard_service.schemas.responses import (
    CandidateItem,
    DashboardStatsResponse,
    DashboardSummaryResponse,
    IncidentItem,
    PositionItem,
)
from libs.db.session import get_db
from libs.logging.context import get_correlation_id, set_correlation_id
from libs.schemas.common import ServiceEnvelope

app = FastAPI(title="dashboard-service")


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
        service="dashboard-service",
        correlation_id=correlation_id,
        data={"status": "healthy"},
        error=None,
    )


@app.get("/v1/dashboard/summary")
def dashboard_summary(request: Request, db: Session = Depends(get_db)) -> ServiceEnvelope[DashboardSummaryResponse]:
    correlation_id = request.headers.get("X-Correlation-Id") or get_correlation_id()
    repo = DashboardRepository(db)
    result = get_dashboard_summary_use_case(repo)
    return ServiceEnvelope[DashboardSummaryResponse](
        ok=True,
        service="dashboard-service",
        correlation_id=correlation_id,
        data=DashboardSummaryResponse(**result),
        error=None,
    )


@app.get("/v1/dashboard/stats")
def dashboard_stats(request: Request, db: Session = Depends(get_db)) -> ServiceEnvelope[DashboardStatsResponse]:
    correlation_id = request.headers.get("X-Correlation-Id") or get_correlation_id()
    repo = StatsRepository(db)
    result = get_dashboard_stats_use_case(repo)
    return ServiceEnvelope[DashboardStatsResponse](
        ok=True,
        service="dashboard-service",
        correlation_id=correlation_id,
        data=DashboardStatsResponse(**result),
        error=None,
    )


@app.get("/v1/dashboard/candidates")
def dashboard_candidates(request: Request, db: Session = Depends(get_db)) -> ServiceEnvelope[list[CandidateItem]]:
    correlation_id = request.headers.get("X-Correlation-Id") or get_correlation_id()
    repo = DashboardRepository(db)
    items = [CandidateItem(**item) for item in list_dashboard_candidates_use_case(repo)]
    return ServiceEnvelope[list[CandidateItem]](
        ok=True,
        service="dashboard-service",
        correlation_id=correlation_id,
        data=items,
        error=None,
    )


@app.get("/v1/dashboard/positions")
def dashboard_positions(request: Request, db: Session = Depends(get_db)) -> ServiceEnvelope[list[PositionItem]]:
    correlation_id = request.headers.get("X-Correlation-Id") or get_correlation_id()
    repo = DashboardRepository(db)
    items = [PositionItem(**item) for item in list_dashboard_positions_use_case(repo)]
    return ServiceEnvelope[list[PositionItem]](
        ok=True,
        service="dashboard-service",
        correlation_id=correlation_id,
        data=items,
        error=None,
    )


@app.get("/v1/dashboard/incidents")
def dashboard_incidents(request: Request, db: Session = Depends(get_db)) -> ServiceEnvelope[list[IncidentItem]]:
    correlation_id = request.headers.get("X-Correlation-Id") or get_correlation_id()
    repo = DashboardRepository(db)
    items = [IncidentItem(**item) for item in list_dashboard_incidents_use_case(repo, limit=50)]
    return ServiceEnvelope[list[IncidentItem]](
        ok=True,
        service="dashboard-service",
        correlation_id=correlation_id,
        data=items,
        error=None,
    )
