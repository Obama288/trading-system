from __future__ import annotations

from apps.journal_review.domain.summary import JournalSummary
from apps.journal_review.infrastructure.journal_reader import JournalReader
from apps.journal_review.infrastructure.llm_client import LLMClient
from apps.journal_review.schemas.requests import PatternReviewRequest


def pattern_review_use_case(
    *,
    journal_reader: JournalReader,
    llm_client: LLMClient,
    req: PatternReviewRequest,
) -> dict:
    events = journal_reader.read_window(
        start_at=req.start_at,
        end_at=req.end_at,
        limit=req.limit,
        event_type=req.event_type,
    )
    llm_result = llm_client.review_patterns(
        events=events,
        start_at=req.start_at.isoformat(),
        end_at=req.end_at.isoformat(),
        event_type=req.event_type,
    )
    summary = JournalSummary(
        advisory_note="Advisory output only. Pattern review cannot approve, reject, or execute trades.",
        summary_text=str(llm_result.get("summary_text", "")),
        key_patterns=[str(item) for item in llm_result.get("key_patterns", [])],
        recurring_risks=[str(item) for item in llm_result.get("recurring_risks", [])],
        suggested_focus=[str(item) for item in llm_result.get("suggested_focus", [])],
        event_count=len(events),
        window_start=req.start_at.isoformat(),
        window_end=req.end_at.isoformat(),
    )
    return summary.to_dict()
