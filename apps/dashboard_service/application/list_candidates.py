from __future__ import annotations

from apps.dashboard_service.infrastructure.dashboard_repo import DashboardRepository


def list_dashboard_candidates_use_case(repo: DashboardRepository) -> list[dict]:
    return repo.list_candidates()
