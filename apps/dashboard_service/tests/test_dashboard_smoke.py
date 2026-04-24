from __future__ import annotations

from apps.dashboard_service.application.get_summary import get_dashboard_summary_use_case
from apps.dashboard_service.application.list_candidates import list_dashboard_candidates_use_case
from apps.dashboard_service.application.list_incidents import list_dashboard_incidents_use_case
from apps.dashboard_service.application.list_positions import list_dashboard_positions_use_case
from apps.dashboard_service.application.stats import get_dashboard_stats_use_case


class DummyRepository:
    def get_summary(self) -> dict:
        return {
            "kill_switch_active": False,
            "pending_candidates_count": 3,
            "open_positions_count": 2,
            "recent_incidents_count": 1,
            "recent_journal_events_count": 8,
        }

    def list_candidates(self) -> list[dict]:
        return [{"candidate_id": "cand_001", "status": "pending"}]

    def list_open_positions(self) -> list[dict]:
        return [{"position_id": "pos_001", "status": "open"}]

    def list_incidents(self, *, limit: int = 50) -> list[dict]:
        return [{"incident_id": "inc_001", "severity": "warning", "limit_used": limit}]

    def get_stats(self, mode: str = "paper") -> dict:
        return {
            "total_trades": 2,
            "win_rate_pct": 50.0,
            "avg_rr": 0.25,
            "total_pnl_usdt": 10.0,
            "avg_hold_candles": 0.0,
            "by_symbol": {
                "BTCUSDT": {
                    "total_trades": 1,
                    "win_rate_pct": 100.0,
                    "avg_rr": 1.0,
                    "total_pnl_usdt": 20.0,
                    "avg_hold_candles": 0.0,
                }
            },
            "by_setup_type": {
                "unknown": {
                    "total_trades": 2,
                    "win_rate_pct": 50.0,
                    "avg_rr": 0.25,
                    "total_pnl_usdt": 10.0,
                    "avg_hold_candles": 0.0,
                }
            },
        }


def test_get_dashboard_summary_use_case_returns_expected_keys():
    repo = DummyRepository()

    result = get_dashboard_summary_use_case(repo)

    assert result == {
        "kill_switch_active": False,
        "pending_candidates_count": 3,
        "open_positions_count": 2,
        "recent_incidents_count": 1,
        "recent_journal_events_count": 8,
    }


def test_list_dashboard_candidates_use_case_returns_list():
    repo = DummyRepository()

    result = list_dashboard_candidates_use_case(repo)

    assert isinstance(result, list)
    assert result == [{"candidate_id": "cand_001", "status": "pending"}]


def test_list_dashboard_positions_use_case_returns_list():
    repo = DummyRepository()

    result = list_dashboard_positions_use_case(repo)

    assert isinstance(result, list)
    assert result == [{"position_id": "pos_001", "status": "open"}]


def test_list_dashboard_incidents_use_case_returns_list():
    repo = DummyRepository()

    result = list_dashboard_incidents_use_case(repo, limit=50)

    assert isinstance(result, list)
    assert result == [{"incident_id": "inc_001", "severity": "warning", "limit_used": 50}]


def test_get_dashboard_stats_use_case_returns_expected_keys():
    repo = DummyRepository()

    result = get_dashboard_stats_use_case(repo)

    assert result["total_trades"] == 2
    assert result["win_rate_pct"] == 50.0
    assert result["avg_rr"] == 0.25
    assert result["total_pnl_usdt"] == 10.0
    assert result["avg_hold_candles"] == 0.0
    assert "by_symbol" in result
    assert "by_setup_type" in result
