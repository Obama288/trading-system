from __future__ import annotations

from pydantic import BaseModel, Field

from libs.schemas.common import ExecutionCandidate


class PlaceExecutionRequest(BaseModel):
    candidate_id: str
    execution_candidate: ExecutionCandidate
    execution_idempotency_key: str = Field(min_length=1)
    correlation_id: str


class CancelExecutionRequest(BaseModel):
    execution_id: str
    correlation_id: str
