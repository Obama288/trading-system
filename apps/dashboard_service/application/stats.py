from __future__ import annotations

from apps.dashboard_service.infrastructure.stats_repo import StatsRepository


def get_dashboard_stats_use_case(repo: StatsRepository) -> dict:
    return repo.get_stats()
