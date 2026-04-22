from __future__ import annotations

from apps.dashboard_service.infrastructure.dashboard_repo import DashboardRepository


def list_dashboard_incidents_use_case(repo: DashboardRepository, *, limit: int = 50) -> list[dict]:
    return repo.list_incidents(limit=limit)
