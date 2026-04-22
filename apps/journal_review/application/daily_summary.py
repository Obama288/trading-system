from __future__ import annotations

from apps.journal_review.domain.summary import JournalSummary
from apps.journal_review.infrastructure.journal_reader import JournalReader
from apps.journal_review.infrastructure.llm_client import LLMClient
from apps.journal_review.schemas.requests import DailySummaryRequest


def daily_summary_use_case(
    *,
    journal_reader: JournalReader,
    llm_client: LLMClient,
    req: DailySummaryRequest,
) -> dict:
    events = journal_reader.read_window(
        start_at=req.start_at,
        end_at=req.end_at,
        limit=req.limit,
    )
    llm_result = llm_client.summarize_journal(
        events=events,
        start_at=req.start_at.isoformat(),
        end_at=req.end_at.isoformat(),
    )
    summary = JournalSummary(
        advisory_note="Advisory output only. This summary cannot trigger execution or alter the pipeline.",
        summary_text=str(llm_result.get("summary_text", "")),
        key_patterns=[str(item) for item in llm_result.get("key_patterns", [])],
        recurring_risks=[str(item) for item in llm_result.get("recurring_risks", [])],
        suggested_focus=[str(item) for item in llm_result.get("suggested_focus", [])],
        event_count=len(events),
        window_start=req.start_at.isoformat(),
        window_end=req.end_at.isoformat(),
    )
    return summary.to_dict()
