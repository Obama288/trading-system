from __future__ import annotations

from apps.incidents.infrastructure.incident_repo import IncidentRepository
from apps.incidents.infrastructure.journal_client import JournalClient
from apps.incidents.schemas.requests import RecordIncidentRequest


def record_incident_use_case(
    *,
    repo: IncidentRepository,
    journal_client: JournalClient,
    req: RecordIncidentRequest,
) -> dict:
    row = repo.create_incident(
        incident_type=req.incident_type.value,
        severity=req.severity.value,
        source_service=req.source_service,
        message=req.message,
        correlation_id=req.correlation_id,
        payload=req.payload,
    )
    incident = repo.to_dict(row)
    journal_client.write(
        {
            "event_id": f"evt_incident_{row.incident_id}",
            "event_type": "incident_recorded",
            "severity": row.severity,
            "correlation_id": row.correlation_id,
            "payload": incident,
        }
    )
    return {"ok": True, "code": "INCIDENT_RECORDED", "incident": incident}
