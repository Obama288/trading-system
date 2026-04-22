from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.journal_ingest.schemas.journal_requests import JournalEventRequest
from apps.journal_ingest.schemas.journal_responses import JournalQueryResult, JournalWriteResult
from libs.db.models.journal_event import JournalEventModel
from libs.db.session import get_db

router = APIRouter()


@router.post("/v1/journal/events", response_model=JournalWriteResult)
def write_event(req: JournalEventRequest, db: Session = Depends(get_db)) -> JournalWriteResult:
    row = JournalEventModel(
        event_id=req.event_id,
        event_type=req.event_type,
        severity=req.severity.value,
        correlation_id=req.correlation_id,
        payload=req.payload,
    )
    db.add(row)
    db.commit()
    return JournalWriteResult(ok=True, event_id=req.event_id)


@router.get("/v1/journal/events", response_model=JournalQueryResult)
def query_events(
    event_type: str | None = None,
    correlation_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> JournalQueryResult:
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    filters = []
    if event_type is not None:
        filters.append(JournalEventModel.event_type == event_type)
    if correlation_id is not None:
        filters.append(JournalEventModel.correlation_id == correlation_id)

    items_stmt = (
        select(JournalEventModel)
        .where(*filters)
        .order_by(JournalEventModel.created_at.desc(), JournalEventModel.event_id.desc())
        .limit(limit)
        .offset(offset)
    )
    total_stmt = select(func.count()).select_from(JournalEventModel).where(*filters)

    rows = db.execute(items_stmt).scalars().all()
    total = db.execute(total_stmt).scalar_one()

    return JournalQueryResult(
        ok=True,
        items=[
            {
                "event_id": row.event_id,
                "event_type": row.event_type,
                "severity": row.severity,
                "correlation_id": row.correlation_id,
                "payload": row.payload,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
        total=total,
    )


@router.get("/health")
def health() -> dict:
    return {"service": "journal-ingest", "status": "healthy"}
