from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.db.models.system_state import SystemStateModel


class SystemStateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, key: str) -> SystemStateModel | None:
        stmt = select(SystemStateModel).where(SystemStateModel.key == key)
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert_in_session(self, key: str, value_json: dict, updated_by: str | None) -> SystemStateModel:
        row = self.get(key)
        if row is None:
            row = SystemStateModel(key=key, value_json=value_json, updated_by=updated_by)
            self.db.add(row)
        else:
            row.value_json = value_json
            row.updated_by = updated_by
            row.updated_at = datetime.now(timezone.utc)
        return row

    def upsert(self, key: str, value_json: dict, updated_by: str | None) -> SystemStateModel:
        row = self.upsert_in_session(key, value_json, updated_by)
        self.db.commit()
        self.db.refresh(row)
        return row
