from __future__ import annotations

from pydantic import BaseModel, Field

from apps.incidents.domain.incident import IncidentSeverity, IncidentType


class RecordIncidentRequest(BaseModel):
    incident_type: IncidentType
    severity: IncidentSeverity
    source_service: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)
    correlation_id: str


class ListIncidentsRequest(BaseModel):
    incident_type: IncidentType | None = None
    severity: IncidentSeverity | None = None
    source_service: str | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
