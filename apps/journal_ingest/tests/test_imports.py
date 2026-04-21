def test_schema_import_smoke():
    from apps.journal_ingest.schemas.journal_requests import JournalEventRequest, JournalQueryRequest
    from apps.journal_ingest.schemas.journal_responses import JournalQueryResult, JournalWriteResult
    from libs.schemas.common import SeverityLevel

    payload = JournalEventRequest(
        event_id="evt_test_001",
        event_type="risk_decision",
        severity=SeverityLevel.INFO,
        correlation_id="corr_test_001",
        payload={"approved": True},
    )

    assert JournalEventRequest is not None
    assert JournalQueryRequest is not None
    assert JournalWriteResult is not None
    assert JournalQueryResult is not None
    assert payload.event_id == "evt_test_001"
    assert payload.severity == SeverityLevel.INFO
