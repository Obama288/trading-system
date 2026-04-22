from datetime import datetime, timezone

from apps.journal_review.application.pattern_review import pattern_review_use_case
from apps.journal_review.schemas.requests import PatternReviewRequest


class DummyJournalReader:
    def __init__(self, events: list[dict]) -> None:
        self.events = events

    def read_window(self, *, start_at, end_at, limit, event_type=None):
        assert event_type == "position_closed"
        return self.events[:limit]


class DummyLLMClient:
    def review_patterns(self, *, events: list[dict], start_at: str, end_at: str, event_type: str | None = None) -> dict:
        assert len(events) == 2
        assert event_type == "position_closed"
        return {
            "summary_text": "Advisory review found repeated stop-loss exits.",
            "key_patterns": ["multiple stop-loss exits occurred in the same regime"],
            "recurring_risks": ["risk exits cluster after volatility spikes"],
            "suggested_focus": ["review whether stop placement is systematically too tight"],
        }


def test_pattern_review_returns_advisory_output():
    start_at = datetime(2026, 4, 20, 0, 0, tzinfo=timezone.utc)
    end_at = datetime(2026, 4, 20, 23, 59, tzinfo=timezone.utc)
    result = pattern_review_use_case(
        journal_reader=DummyJournalReader(
            [
                {"event_id": "evt_010", "event_type": "position_closed"},
                {"event_id": "evt_011", "event_type": "position_closed"},
            ]
        ),
        llm_client=DummyLLMClient(),
        req=PatternReviewRequest(
            start_at=start_at,
            end_at=end_at,
            event_type="position_closed",
            limit=100,
            correlation_id="corr_002",
        ),
    )

    assert result["advisory_note"].startswith("Advisory output only.")
    assert result["event_count"] == 2
    assert result["summary_text"] == "Advisory review found repeated stop-loss exits."
    assert result["suggested_focus"] == ["review whether stop placement is systematically too tight"]
