from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from apps.execution_service.application.detect_orphans import detect_orphan_executions_use_case_async
from apps.execution_service.infrastructure.local_clients import DbJournalClient, NoopAlertClient
from apps.execution_service.infrastructure.position_admission_repo import DbPositionAdmissionRepo

LOGGER = logging.getLogger(__name__)

_ESCALATION_THRESHOLD = 3
_MAX_BACKOFF_FACTOR = 8


async def run_orphan_scheduler_loop(
    *,
    session_factory,
    interval_seconds: float = 60.0,
    execution_mode: str | None = None,
    continue_on_error: bool = True,
    stop_event: asyncio.Event | None = None,
) -> None:
    consecutive_failures = 0
    while True:
        if stop_event is not None and stop_event.is_set():
            return

        db = None
        error_in_cycle: Exception | None = None
        try:
            db = session_factory()
            correlation_id = f"corr_orphan_sched_{uuid4().hex}"
            admission_repo = DbPositionAdmissionRepo(db)
            journal_client = DbJournalClient(db)
            alert_client = NoopAlertClient()

            class DetectorAdapter:
                def get_pending_open_executions(self, mode: str | None = None) -> list:
                    return admission_repo.get_pending_open_executions(mode=mode)

                def get_emitted_orphan_event_ids(self) -> set[str]:
                    from libs.db.models.journal_event import JournalEventModel
                    from sqlalchemy import select as sa_select
                    stmt = (
                        sa_select(JournalEventModel.event_id)
                        .where(JournalEventModel.event_type == "orphan_execution_detected")
                    )
                    return set(db.execute(stmt).scalars().all())

                async def emit_detection_event(self, events: list[dict]) -> None:
                    for evt in events:
                        await journal_client.write(evt)

                async def emit_escalation_event(self, count: int) -> None:
                    if count > 0:
                        await alert_client.notify({
                            "event_type": "orphan_execution_detected",
                            "service": "execution-service",
                            "source": "orphan_scheduler",
                            "orphan_count": count,
                        })

                def get_correlation_id(self) -> str:
                    return correlation_id

                def get_journal_client(self):
                    return journal_client

            result = await detect_orphan_executions_use_case_async(
                detector=DetectorAdapter(),
                mode=execution_mode,
                emit_events=True,
                correlation_id=correlation_id,
            )
            consecutive_failures = 0
            LOGGER.info(
                "orphan scheduler cycle completed",
                extra={
                    "correlation_id": correlation_id,
                    "orphan_count": result.get("orphan_count"),
                    "new_orphan_count": result.get("new_orphan_count"),
                },
            )
        except Exception as exc:
            error_in_cycle = exc
            consecutive_failures += 1
            LOGGER.exception(
                "orphan scheduler cycle failed",
                extra={"consecutive_failures": consecutive_failures},
            )
            if consecutive_failures >= _ESCALATION_THRESHOLD:
                LOGGER.error(
                    "orphan scheduler repeated failure — operator action may be required",
                    extra={"consecutive_failures": consecutive_failures, "error": str(exc)},
                )
        finally:
            if db is not None:
                db.close()

        if error_in_cycle is not None:
            if not continue_on_error:
                raise error_in_cycle
            backoff_seconds = min(
                interval_seconds * (2 ** (consecutive_failures - 1)),
                interval_seconds * _MAX_BACKOFF_FACTOR,
            )
            await asyncio.sleep(backoff_seconds)
            continue

        await asyncio.sleep(interval_seconds)
