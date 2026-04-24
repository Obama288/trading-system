from __future__ import annotations

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.execution_service.application.orphan_scheduler import run_orphan_scheduler_loop
from libs.db.base import Base


@pytest.fixture()
def sqlite_session_factory() -> Generator[sessionmaker, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)


class TestOrphanSchedulerStop:
    @pytest.mark.asyncio
    async def test_exits_immediately_when_stop_event_preset(self):
        stop = asyncio.Event()
        stop.set()
        calls = []

        def session_factory():
            calls.append(1)
            raise RuntimeError("should not be called")

        await run_orphan_scheduler_loop(session_factory=session_factory, stop_event=stop)
        assert calls == []

    @pytest.mark.asyncio
    async def test_exits_after_stop_event_set_between_cycles(self, sqlite_session_factory):
        stop = asyncio.Event()
        cycles = [0]

        async def _fake_detect(**kwargs):
            cycles[0] += 1
            stop.set()
            return {"ok": True, "orphan_count": 0, "new_orphan_count": 0,
                    "already_signaled_count": 0, "execution_ids": [], "mode": None,
                    "correlation_id": "corr_test", "code": "ORPHAN_DETECTION_COMPLETE"}

        with patch(
            "apps.execution_service.application.orphan_scheduler.detect_orphan_executions_use_case_async",
            _fake_detect,
        ):
            await run_orphan_scheduler_loop(
                session_factory=sqlite_session_factory,
                interval_seconds=0,
                stop_event=stop,
                continue_on_error=False,
            )

        assert cycles[0] == 1


class TestOrphanSchedulerErrorHandling:
    @pytest.mark.asyncio
    async def test_raises_on_first_failure_when_continue_on_error_false(self):
        def failing_session_factory():
            raise RuntimeError("db down")

        with pytest.raises(RuntimeError, match="db down"):
            await run_orphan_scheduler_loop(
                session_factory=failing_session_factory,
                interval_seconds=0,
                continue_on_error=False,
            )

    @pytest.mark.asyncio
    async def test_continues_after_failure_when_continue_on_error_true(self):
        stop = asyncio.Event()
        call_count = [0]

        def failing_session_factory():
            call_count[0] += 1
            if call_count[0] >= 3:
                stop.set()
            raise RuntimeError("transient error")

        # Should not raise even though all cycles fail
        await run_orphan_scheduler_loop(
            session_factory=failing_session_factory,
            interval_seconds=0,
            continue_on_error=True,
            stop_event=stop,
        )
        assert call_count[0] >= 3

    @pytest.mark.asyncio
    async def test_logs_error_at_escalation_threshold(self, caplog):
        import logging
        stop = asyncio.Event()
        call_count = [0]

        def failing_session_factory():
            call_count[0] += 1
            if call_count[0] > 3:
                stop.set()
            raise RuntimeError("persistent failure")

        with caplog.at_level(logging.ERROR, logger="apps.execution_service.application.orphan_scheduler"):
            await run_orphan_scheduler_loop(
                session_factory=failing_session_factory,
                interval_seconds=0,
                continue_on_error=True,
                stop_event=stop,
            )

        escalation_logs = [r for r in caplog.records if "repeated failure" in r.message]
        assert len(escalation_logs) >= 1


class TestOrphanSchedulerCleanCycle:
    @pytest.mark.asyncio
    async def test_clean_cycle_logs_completion(self, sqlite_session_factory, caplog):
        import logging
        stop = asyncio.Event()

        async def _fake_detect(**kwargs):
            stop.set()
            return {"ok": True, "orphan_count": 0, "new_orphan_count": 0,
                    "already_signaled_count": 0, "execution_ids": [], "mode": None,
                    "correlation_id": "corr_test", "code": "ORPHAN_DETECTION_COMPLETE"}

        with caplog.at_level(logging.INFO, logger="apps.execution_service.application.orphan_scheduler"):
            with patch(
                "apps.execution_service.application.orphan_scheduler.detect_orphan_executions_use_case_async",
                _fake_detect,
            ):
                await run_orphan_scheduler_loop(
                    session_factory=sqlite_session_factory,
                    interval_seconds=0,
                    stop_event=stop,
                    continue_on_error=False,
                )

        completion_logs = [r for r in caplog.records if "cycle completed" in r.message]
        assert len(completion_logs) == 1
