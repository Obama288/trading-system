from __future__ import annotations

from fastapi import APIRouter

from apps.journal_ingest.schemas.journal_requests import JournalEventRequest, JournalQueryRequest
from apps.journal_ingest.schemas.journal_responses import JournalQueryResult, JournalWriteResult

router = APIRouter()


@router.post("/v1/journal/events", response_model=JournalWriteResult)
def write_event(req: JournalEventRequest) -> JournalWriteResult:
    return JournalWriteResult(ok=True, event_id=req.event_id)


@router.get("/v1/journal/events", response_model=JournalQueryResult)
def query_events(event_type: str | None = None, correlation_id: str | None = None, limit: int = 50, offset: int = 0) -> JournalQueryResult:
    return JournalQueryResult(ok=True, items=[], total=0)


@router.get("/health")
def health() -> dict:
    return {"service": "journal-ingest", "status": "healthy"}
