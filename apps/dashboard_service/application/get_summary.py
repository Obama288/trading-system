from __future__ import annotations

from apps.dashboard_service.infrastructure.dashboard_repo import DashboardRepository


def get_dashboard_summary_use_case(repo: DashboardRepository) -> dict:
    return repo.get_summary()
