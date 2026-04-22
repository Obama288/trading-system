from datetime import datetime, timezone

from apps.journal_review.application.daily_summary import daily_summary_use_case
from apps.journal_review.schemas.requests import DailySummaryRequest


class DummyJournalReader:
    def __init__(self, events: list[dict]) -> None:
        self.events = events

    def read_window(self, *, start_at, end_at, limit, event_type=None):
        assert event_type is None
        return self.events[:limit]


class DummyLLMClient:
    def summarize_journal(self, *, events: list[dict], start_at: str, end_at: str) -> dict:
        assert len(events) == 2
        assert start_at.endswith("+00:00")
        assert end_at.endswith("+00:00")
        return {
            "summary_text": "Two advisory observations from journal activity.",
            "key_patterns": ["candidate approvals cluster early in session"],
            "recurring_risks": ["handoff failures repeat after approval"],
            "suggested_focus": ["audit approval-to-execution latency"],
        }


def test_daily_summary_returns_advisory_output():
    start_at = datetime(2026, 4, 20, 0, 0, tzinfo=timezone.utc)
    end_at = datetime(2026, 4, 20, 23, 59, tzinfo=timezone.utc)
    result = daily_summary_use_case(
        journal_reader=DummyJournalReader(
            [
                {"event_id": "evt_001", "event_type": "candidate_created"},
                {"event_id": "evt_002", "event_type": "candidate_approved"},
            ]
        ),
        llm_client=DummyLLMClient(),
        req=DailySummaryRequest(
            start_at=start_at,
            end_at=end_at,
            limit=100,
            correlation_id="corr_001",
        ),
    )

    assert result["advisory_note"].startswith("Advisory output only.")
    assert result["event_count"] == 2
    assert result["key_patterns"] == ["candidate approvals cluster early in session"]
    assert result["recurring_risks"] == ["handoff failures repeat after approval"]
