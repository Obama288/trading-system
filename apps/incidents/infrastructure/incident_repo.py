from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.db.models.incident import IncidentModel


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_incident(
        self,
        *,
        incident_type: str,
        severity: str,
        source_service: str,
        message: str,
        correlation_id: str,
        payload: dict,
    ) -> IncidentModel:
        model = IncidentModel(
            incident_id=f"inc_{uuid4().hex}",
            incident_type=incident_type,
            severity=severity,
            source_service=source_service,
            message=message,
            correlation_id=correlation_id,
            payload=payload,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def list_incidents(
        self,
        *,
        incident_type: str | None = None,
        severity: str | None = None,
        source_service: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[IncidentModel]:
        stmt = select(IncidentModel)
        if incident_type is not None:
            stmt = stmt.where(IncidentModel.incident_type == incident_type)
        if severity is not None:
            stmt = stmt.where(IncidentModel.severity == severity)
        if source_service is not None:
            stmt = stmt.where(IncidentModel.source_service == source_service)
        stmt = stmt.order_by(IncidentModel.created_at.desc(), IncidentModel.incident_id.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def get_incident(self, incident_id: str) -> IncidentModel | None:
        stmt = select(IncidentModel).where(IncidentModel.incident_id == incident_id)
        return self.db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def to_dict(model: IncidentModel) -> dict:
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
