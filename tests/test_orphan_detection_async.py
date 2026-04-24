from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.execution_service.application.detect_orphans import detect_orphan_executions_use_case_async


class MockOrphan:
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.idempotency_key = f"key_{execution_id}"
        self.candidate_id = f"cand_{execution_id}"
        self.status = "pending_open"
        self.mode = "paper"
        self.payload = {}
        self.created_at = "2026-01-01T00:00:00"


class TestOrphanDetectionAsync:
    @pytest.mark.asyncio
    async def test_writes_journal_event_on_detection(self):
        journal_calls = []
        alert_calls = []

        class MockDetector:
            def get_pending_open_executions(self, mode=None):
                return [MockOrphan("exec-1"), MockOrphan("exec-2")]

            def get_emitted_orphan_event_ids(self):
                return set()

            async def emit_detection_event(self, events):
                journal_calls.extend(events)

            async def emit_escalation_event(self, count):
                alert_calls.append(count)

            def get_correlation_id(self):
                return "test-corr-123"

        result = await detect_orphan_executions_use_case_async(
            detector=MockDetector(),
            mode="paper",
            emit_events=True,
        )

        assert result["orphan_count"] == 2
        assert result["new_orphan_count"] == 2
        assert len(journal_calls) == 2
        assert journal_calls[0]["event_type"] == "orphan_execution_detected"
        assert journal_calls[0]["event_id"] == "evt_orphan_execution_detected_exec-1"

    @pytest.mark.asyncio
    async def test_dedup_skips_already_emitted(self):
        journal_calls = []

        class MockDetector:
            def get_pending_open_executions(self, mode=None):
                return [MockOrphan("exec-1")]

            def get_emitted_orphan_event_ids(self):
                return {"evt_orphan_execution_detected_exec-1"}

            async def emit_detection_event(self, events):
                journal_calls.extend(events)

            async def emit_escalation_event(self, count):
                pass

            def get_correlation_id(self):
                return "test-corr-123"

        result = await detect_orphan_executions_use_case_async(
            detector=MockDetector(),
            mode="paper",
            emit_events=True,
        )

        assert result["new_orphan_count"] == 0
        assert result["already_signaled_count"] == 1
        assert len(journal_calls) == 0

    @pytest.mark.asyncio
    async def test_alert_called_when_orphans_found(self):
        alert_called = []

        class MockDetector:
            def get_pending_open_executions(self, mode=None):
                return [MockOrphan("exec-1")]

            def get_emitted_orphan_event_ids(self):
                return set()

            async def emit_detection_event(self, events):
                pass

            async def emit_escalation_event(self, count):
                alert_called.append(count)

            def get_correlation_id(self):
                return "test-corr-123"

        result = await detect_orphan_executions_use_case_async(
            detector=MockDetector(),
            mode="paper",
            emit_events=True,
        )

        assert alert_called == [1]

    @pytest.mark.asyncio
    async def test_no_alert_when_no_orphans(self):
        alert_called = []

        class MockDetector:
            def get_pending_open_executions(self, mode=None):
                return []

            def get_emitted_orphan_event_ids(self):
                return set()

            async def emit_detection_event(self, events):
                pass

            async def emit_escalation_event(self, count):
                alert_called.append(count)

            def get_correlation_id(self):
                return "test-corr-123"

        result = await detect_orphan_executions_use_case_async(
            detector=MockDetector(),
            mode="paper",
            emit_events=True,
        )

        assert result["orphan_count"] == 0
        assert alert_called == []