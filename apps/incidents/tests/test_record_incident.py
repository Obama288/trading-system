from datetime import datetime, timezone

from apps.incidents.application.record_incident import record_incident_use_case
from apps.incidents.domain.incident import IncidentSeverity, IncidentType
from apps.incidents.schemas.requests import RecordIncidentRequest


class DummyRow:
    def __init__(self) -> None:
        self.incident_id = "inc_001"
        self.incident_type = "execution_failed"
        self.severity = "error"
        self.source_service = "execution-service"
        self.message = "order was rejected"
        self.correlation_id = "corr_001"
        self.payload = {"execution_id": "exe_001"}
        self.created_at = datetime(2026, 4, 21, 10, 0, tzinfo=timezone.utc)


class DummyRepo:
    def __init__(self) -> None:
        self.created: list[dict] = []

    def create_incident(self, **kwargs):
        self.created.append(kwargs)
        return DummyRow()

    def to_dict(self, model):
        return {
            "incident_id": model.incident_id,
            "incident_type": model.incident_type,
            "severity": model.severity,
            "source_service": model.source_service,
            "message": model.message,
            "correlation_id": model.correlation_id,
            "payload": model.payload,
            "created_at": model.created_at.isoformat(),
        }


class DummyJournalClient:
    def __init__(self) -> None:
        self.writes: list[dict] = []

    def write(self, payload: dict) -> None:
        self.writes.append(payload)


def test_record_incident_persists_and_writes_journal():
    repo = DummyRepo()
    journal = DummyJournalClient()

    result = record_incident_use_case(
        repo=repo,
        journal_client=journal,
        req=RecordIncidentRequest(
            incident_type=IncidentType.EXECUTION_FAILED,
            severity=IncidentSeverity.ERROR,
            source_service="execution-service",
            message="order was rejected",
            payload={"execution_id": "exe_001"},
            correlation_id="corr_001",
        ),
    )

    assert result["ok"] is True
    assert result["code"] == "INCIDENT_RECORDED"
    assert repo.created[0]["incident_type"] == "execution_failed"
    assert len(journal.writes) == 1
    assert journal.writes[0]["event_type"] == "incident_recorded"
