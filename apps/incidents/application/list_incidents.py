from __future__ import annotations

from apps.incidents.infrastructure.incident_repo import IncidentRepository
from apps.incidents.schemas.requests import ListIncidentsRequest


def list_incidents_use_case(*, repo: IncidentRepository, req: ListIncidentsRequest) -> dict:
    items = repo.list_incidents(
        incident_type=req.incident_type.value if req.incident_type else None,
        severity=req.severity.value if req.severity else None,
        source_service=req.source_service,
        limit=req.limit,
        offset=req.offset,
    )
    return {
        "ok": True,
        "items": [repo.to_dict(row) for row in items],
        "limit": req.limit,
        "offset": req.offset,
    }
