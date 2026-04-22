from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class IncidentSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    EXCHANGE_DISCONNECT = "exchange_disconnect"
    POSITION_MISMATCH = "position_mismatch"
    RISK_UNAVAILABLE = "risk_unavailable"
    REVIEW_UNAVAILABLE = "review_unavailable"
    STALE_MARKET_DATA = "stale_market_data"
    KILL_SWITCH_ACTIVATED = "kill_switch_activated"
    EXECUTION_FAILED = "execution_failed"
    JOURNAL_WRITE_FAILED = "journal_write_failed"


@dataclass(slots=True)
class Incident:
    incident_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    source_service: str
    message: str
    correlation_id: str
    created_at: datetime
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "incident_type": self.incident_type.value,
            "severity": self.severity.value,
            "source_service": self.source_service,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }
