from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class OrphanExecution:
    execution_id: str
    idempotency_key: str
    candidate_id: str
    status: str
    mode: str
    payload: dict
    created_at: str


class OrphanDetector(Protocol):
    def get_pending_open_executions(self, *, mode: str | None = None) -> list[dict]: ...

    def get_emitted_orphan_event_ids(self) -> set[str]: ...

    async def emit_detection_event(self, orphans: list[dict]) -> None: ...

    async def emit_escalation_event(self, count: int) -> None: ...

    def get_correlation_id(self) -> str: ...

    def get_journal_client(self): ...


def detect_orphan_executions_use_case_sync(
    *,
    detector: OrphanDetector,
    mode: str | None = None,
    emit_events: bool = True,
    correlation_id: str | None = None,
) -> dict:
    orphans = detector.get_pending_open_executions(mode=mode)
    corr = correlation_id or detector.get_correlation_id()

    orphaned_executions = [
        OrphanExecution(
            execution_id=o.execution_id,
            idempotency_key=o.idempotency_key,
            candidate_id=o.candidate_id,
            status=o.status,
            mode=o.mode,
            payload=o.payload,
            created_at=o.created_at,
        )
        for o in orphans
    ]

    already_emitted = detector.get_emitted_orphan_event_ids() if emit_events else set()
    already_emitted_execution_ids = {
        eid.replace("evt_orphan_execution_detected_", "") for eid in already_emitted
    }
    new_orphans = [o for o in orphaned_executions if o.execution_id not in already_emitted_execution_ids]

    if emit_events and new_orphans:
        detector.emit_detection_event(
            [
                {
                    "event_id": f"evt_orphan_execution_detected_{o.execution_id}",
                    "event_type": "orphan_execution_detected",
                    "severity": "warning",
                    "correlation_id": corr,
                    "payload": {
                        "execution_id": o.execution_id,
                        "candidate_id": o.candidate_id,
                        "mode": o.mode,
                        "created_at": o.created_at,
                    },
                }
                for o in new_orphans
            ]
        )
        detector.emit_escalation_event(count=len(new_orphans))

    return {
        "ok": True,
        "code": "ORPHAN_DETECTION_COMPLETE",
        "orphan_count": len(orphaned_executions),
        "new_orphan_count": len(new_orphans),
        "already_signaled_count": len(orphaned_executions) - len(new_orphans),
        "execution_ids": [o.execution_id for o in orphaned_executions],
        "mode": mode,
        "correlation_id": corr,
    }


async def detect_orphan_executions_use_case_async(
    *,
    detector: OrphanDetector,
    mode: str | None = None,
    emit_events: bool = True,
    correlation_id: str | None = None,
) -> dict:
    orphans = detector.get_pending_open_executions(mode=mode)
    corr = correlation_id or detector.get_correlation_id()

    orphaned_executions = [
        OrphanExecution(
            execution_id=o.execution_id,
            idempotency_key=o.idempotency_key,
            candidate_id=o.candidate_id,
            status=o.status,
            mode=o.mode,
            payload=o.payload,
            created_at=o.created_at,
        )
        for o in orphans
    ]

    already_emitted = detector.get_emitted_orphan_event_ids() if emit_events else set()
    already_emitted_execution_ids = {
        eid.replace("evt_orphan_execution_detected_", "") for eid in already_emitted
    }
    new_orphans = [o for o in orphaned_executions if o.execution_id not in already_emitted_execution_ids]

    if emit_events and new_orphans:
        await detector.emit_detection_event(
            [
                {
                    "event_id": f"evt_orphan_execution_detected_{o.execution_id}",
                    "event_type": "orphan_execution_detected",
                    "severity": "warning",
                    "correlation_id": corr,
                    "payload": {
                        "execution_id": o.execution_id,
                        "candidate_id": o.candidate_id,
                        "mode": o.mode,
                        "created_at": o.created_at,
                    },
                }
                for o in new_orphans
            ]
        )
        await detector.emit_escalation_event(count=len(new_orphans))

    return {
        "ok": True,
        "code": "ORPHAN_DETECTION_COMPLETE",
        "orphan_count": len(orphaned_executions),
        "new_orphan_count": len(new_orphans),
        "already_signaled_count": len(orphaned_executions) - len(new_orphans),
        "execution_ids": [o.execution_id for o in orphaned_executions],
        "mode": mode,
        "correlation_id": corr,
    }