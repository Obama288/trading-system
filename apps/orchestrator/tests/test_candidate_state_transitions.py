from datetime import datetime, timedelta, timezone
from typing import Callable

import httpx
import pytest
from sqlalchemy.exc import SQLAlchemyError

from apps.orchestrator.application.approve_candidate import approve_candidate_use_case
from apps.orchestrator.application.create_candidate import create_candidate_use_case
from apps.orchestrator.application.reject_candidate import reject_candidate_use_case
from libs.db.models.journal_event import JournalEventModel
from libs.schemas.common import (
    EntryZone,
    ExecutionCandidate,
    OrderSide,
    ReviewDecision,
    RiskDecision,
    RiskReasonCode,
    SignalDecision,
    SignalStatus,
    TradeDirection,
)


class DummyExecutionClient:
    def __init__(
        self,
        execution_id: str | None = "exe_001",
        *,
        ok: bool = True,
        raises: bool = False,
        error_payload: dict | None = None,
    ) -> None:
        self.execution_id = execution_id
        self.ok = ok
        self.raises = raises
        self.error_payload = error_payload or {"code": "EXECUTION_REJECTED"}
        self.calls = 0

    async def place(self, *, candidate_id: str, execution_candidate: dict, correlation_id: str) -> dict:
        self.calls += 1
        if self.raises:
            raise httpx.HTTPError("execution request failed")
        return {"ok": self.ok, "data": {"execution_id": self.execution_id}, "error": None if self.ok else self.error_payload}


class DummyKillSwitchClient:
    def __init__(self, *, kill_switch_active: bool = False) -> None:
        self.kill_switch_active = kill_switch_active
        self.calls = 0

    async def get_status(self, correlation_id: str) -> dict:
        self.calls += 1
        return {
            "ok": True,
            "service": "kill-switch",
            "version": "v1",
            "correlation_id": correlation_id,
            "data": {
                "trading_enabled": not self.kill_switch_active,
                "kill_switch_active": self.kill_switch_active,
                "incident_code": "manual_halt" if self.kill_switch_active else None,
            },
            "error": None,
        }


class DummyJournalClient:
    def __init__(self) -> None:
        self.writes: list[dict] = []

    async def write(self, payload: dict) -> None:
        self.writes.append(payload)


class FailingJournalClient:
    async def write(self, payload: dict) -> None:
        raise RuntimeError("journal host unavailable")


class DummyOperatorActionRepo:
    def __init__(self, *, db: "_FakeDb | None" = None) -> None:
        self.records: list[dict] = []
        self._pending: list[dict] = []
        if db is not None:
            db.register_hooks(self._on_commit, self._on_rollback)

    def record(self, **kwargs):
        self.records.append(kwargs)
        return kwargs

    def record_no_commit(self, **kwargs):
        self._pending.append(kwargs)
        return kwargs

    def _on_commit(self) -> None:
        self.records.extend(self._pending)
        self._pending = []

    def _on_rollback(self) -> None:
        self._pending = []


class DummyCandidate:
    def __init__(self, status: str = "pending", expired: bool = False):
        self.candidate_id = "cand_001"
        self.status = status
        self.execution_payload_json = {"symbol": "BTCUSDT", "side": "buy"}
        self.ttl_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1) if expired else datetime.now(timezone.utc) + timedelta(seconds=120)


class _FakeBegin:
    def __init__(self, db) -> None:
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.db.commits += 1
            return False
        self.db.rollbacks += 1
        return False


class _FakeDb:
    def __init__(self, *, fail_journal_flush: bool = False) -> None:
        self.fail_journal_flush = fail_journal_flush
        self.added: list[object] = []
        self.commits = 0
        self.rollbacks = 0
        self._on_commit: list[Callable[[], None]] = []
        self._on_rollback: list[Callable[[], None]] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def register_hooks(self, on_commit, on_rollback) -> None:
        self._on_commit.append(on_commit)
        self._on_rollback.append(on_rollback)

    def flush(self) -> None:
        if self.fail_journal_flush and any(isinstance(x, JournalEventModel) for x in self.added):
            raise SQLAlchemyError("simulated journal flush failure")

    def commit(self) -> None:
        self.commits += 1
        for hook in self._on_commit:
            hook()

    def rollback(self) -> None:
        self.rollbacks += 1
        for hook in self._on_rollback:
            hook()

    def refresh(self, _obj: object) -> None:
        return None


class DummyRepo:
    def __init__(self, candidate, *, db: _FakeDb | None = None):
        self.candidate = candidate
        self.marked_failed = False
        self.approve_calls = 0
        self.db = db or _FakeDb()
        self._snapshots: dict[int, dict[str, object]] = {}
        self.db.register_hooks(self._on_commit, self._on_rollback)
        self._by_signal_id: dict[str, object] = {}

    def create_candidate(self, **kwargs):
        # Mimic repo behavior: candidate is staged in the session; commit is owned by the caller.
        self.db.add({"_type": "trade_candidate", "candidate_id": kwargs["candidate_id"]})

        class Row:
            candidate_id = kwargs["candidate_id"]
            signal_id = kwargs["signal_id"]
            risk_id = kwargs["risk_id"]
            review_id = kwargs["review_id"]
            status = "pending"
            ttl_expires_at = kwargs["ttl_expires_at"]
        row = Row()
        self._by_signal_id[kwargs["signal_id"]] = row
        return row

    def get_by_signal_id(self, signal_id: str):
        return self._by_signal_id.get(signal_id)

    def get_candidate(self, candidate_id: str):
        return self.candidate

    def expire_if_needed(self, model):
        if model.status == "pending" and model.ttl_expires_at <= datetime.now(timezone.utc):
            model.status = "expired"
        return model

    def approve_candidate(self, model, telegram_user_id: int):
        self.approve_calls += 1
        model.status = "approved"
        return model

    def approve_candidate_no_commit(self, model, telegram_user_id: int):
        self.approve_calls += 1
        self._snapshot(model, ("status", "approved_by_user_id", "approved_at"))
        model.status = "approved"
        model.approved_by_user_id = telegram_user_id
        model.approved_at = datetime.now(timezone.utc)
        return model

    def reject_candidate(self, model, telegram_user_id: int):
        model.status = "rejected"
        return model

    def reject_candidate_no_commit(self, model, telegram_user_id: int):
        self._snapshot(model, ("status", "rejected_by_user_id", "rejected_at"))
        model.status = "rejected"
        model.rejected_by_user_id = telegram_user_id
        model.rejected_at = datetime.now(timezone.utc)
        return model

    def attach_execution(self, model, execution_id: str):
        model.execution_id = execution_id
        model.status = "submitted"
        return model

    def attach_execution_no_commit(self, model, execution_id: str):
        self._snapshot(model, ("status", "execution_id"))
        model.execution_id = execution_id
        model.status = "submitted"
        return model

    def mark_execution_failed(self, model):
        model.status = "failed_execution"
        model.execution_id = None
        self.marked_failed = True
        return model

    def mark_execution_failed_no_commit(self, model):
        self._snapshot(model, ("status", "execution_id"))
        model.status = "failed_execution"
        model.execution_id = None
        self.marked_failed = True
        return model

    def _snapshot(self, model, fields: tuple[str, ...]) -> None:
        key = id(model)
        if key not in self._snapshots:
            self._snapshots[key] = {}
        for field in fields:
            if field not in self._snapshots[key]:
                self._snapshots[key][field] = getattr(model, field, None)

    def _on_commit(self) -> None:
        self._snapshots = {}

    def _on_rollback(self) -> None:
        for model_key, fields in self._snapshots.items():
            if self.candidate is not None and id(self.candidate) == model_key:
                for field, value in fields.items():
                    setattr(self.candidate, field, value)
        self._snapshots = {}


def make_signal() -> SignalDecision:
    return SignalDecision(
        signal_id="sig_001",
        status=SignalStatus.CANDIDATE,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        setup_type="breakout_retest",
        entry_zone=EntryZone(min=100.0, max=101.0),
        stop_loss=95.0,
        take_profit=[110.0],
        confidence=0.6,
        reasoning_summary="ok",
    )


def make_risk() -> RiskDecision:
    return RiskDecision(
        risk_id="risk_001",
        signal_id="sig_001",
        symbol="BTCUSDT",
        approved=True,
        position_size=1.0,
        notional_usdt=100.0,
        max_loss_usdt=5.0,
        risk_pct_of_equity=0.5,
        leverage=1.0,
        portfolio_exposure_pct=10.0,
        daily_loss_limit_status="ok",
        drawdown_lock=False,
        kill_switch_required=False,
        reason_codes=[RiskReasonCode.RISK_OK],
    )


def make_review(passed: bool = True) -> ReviewDecision:
    candidate = ExecutionCandidate(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="limit",
        entry_price=101.0,
        quantity=1.0,
        stop_loss=95.0,
        take_profit=[110.0],
        time_in_force="GTC",
    )
    return ReviewDecision(
        review_id="rev_001",
        signal_id="sig_001",
        risk_id="risk_001",
        passed=passed,
        anomaly_flags=[],
        review_notes="ok",
        execution_candidate=candidate if passed else None,
    )


def test_create_candidate_success_and_writes_journal():
    repo = DummyRepo(None)
    result = create_candidate_use_case(repo, make_signal(), make_risk(), make_review(True), "corr_001", ttl_seconds=120)
    assert result["ok"] is True
    assert result["code"] == "CANDIDATE_CREATED"
    assert len([x for x in repo.db.added if isinstance(x, JournalEventModel)]) == 1


def test_create_candidate_fails_when_journal_db_write_fails():
    repo = DummyRepo(None, db=_FakeDb(fail_journal_flush=True))
    result = create_candidate_use_case(repo, make_signal(), make_risk(), make_review(True), "corr_001", ttl_seconds=120)
    assert result["ok"] is False
    assert result["code"] == "JOURNAL_WRITE_FAILED"


def test_create_candidate_is_idempotent_on_signal_id():
    repo = DummyRepo(None)
    first = create_candidate_use_case(repo, make_signal(), make_risk(), make_review(True), "corr_001", ttl_seconds=120)
    second = create_candidate_use_case(repo, make_signal(), make_risk(), make_review(True), "corr_002", ttl_seconds=120)

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["code"] == "CANDIDATE_EXISTS"
    assert second["candidate_id"] == first["candidate_id"]


@pytest.mark.asyncio
async def test_approve_candidate_submits_execution_and_writes_audit_and_journal():
    repo = DummyRepo(DummyCandidate())
    audit = DummyOperatorActionRepo(db=repo.db)
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), audit, "cand_001", 123, "corr_001")
    assert result["ok"] is True
    assert result["execution_id"] == "exe_001"
    assert repo.candidate.status == "submitted"
    assert repo.candidate.execution_id == "exe_001"
    assert len(audit.records) == 1
    journal_events = [x for x in repo.db.added if isinstance(x, JournalEventModel)]
    assert len(journal_events) == 1
    assert journal_events[0].event_type == "candidate_approved"


@pytest.mark.asyncio
async def test_approve_candidate_missing_execution_id_writes_failure_journal():
    repo = DummyRepo(DummyCandidate())
    audit = DummyOperatorActionRepo(db=repo.db)
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(execution_id=None), audit, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_SUBMISSION_NO_ID"
    assert repo.candidate.status == "failed_execution"
    assert repo.candidate.execution_id is None
    assert repo.marked_failed is True
    assert len(audit.records) == 1
    journal_events = [x for x in repo.db.added if isinstance(x, JournalEventModel)]
    assert len(journal_events) == 1
    assert journal_events[0].event_type == "execution_failed_after_approval"


@pytest.mark.asyncio
async def test_approve_candidate_execution_not_accepted_rolls_back_candidate():
    repo = DummyRepo(DummyCandidate())
    audit = DummyOperatorActionRepo(db=repo.db)
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(ok=False), audit, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_REJECTED"
    assert result["execution_error_code"] == "EXECUTION_REJECTED"
    assert result["execution_error"]["code"] == "EXECUTION_REJECTED"
    assert repo.candidate.status == "failed_execution"
    assert repo.candidate.execution_id is None
    assert len(audit.records) == 1
    journal_events = [x for x in repo.db.added if isinstance(x, JournalEventModel)]
    assert len(journal_events) == 1
    assert journal_events[0].event_type == "execution_failed_after_approval"
    assert journal_events[0].payload["execution_error_code"] == "EXECUTION_REJECTED"


@pytest.mark.asyncio
async def test_approve_candidate_execution_http_error_rolls_back_candidate():
    repo = DummyRepo(DummyCandidate())
    audit = DummyOperatorActionRepo(db=repo.db)
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(raises=True), audit, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_REQUEST_FAILED"
    assert result["execution_error_code"] == "EXECUTION_REQUEST_FAILED"
    assert result["execution_error"]["code"] == "EXECUTION_REQUEST_FAILED"
    assert repo.candidate.status == "failed_execution"
    assert repo.candidate.execution_id is None
    assert len(audit.records) == 1
    journal_events = [x for x in repo.db.added if isinstance(x, JournalEventModel)]
    assert len(journal_events) == 1
    assert journal_events[0].event_type == "execution_failed_after_approval"
    assert journal_events[0].payload["execution_error_code"] == "EXECUTION_REQUEST_FAILED"


@pytest.mark.asyncio
async def test_approve_candidate_propagates_max_open_reject_reason():
    repo = DummyRepo(DummyCandidate())
    audit = DummyOperatorActionRepo(db=repo.db)
    execution = DummyExecutionClient(
        ok=False,
        error_payload={
            "code": "MAX_OPEN_POSITIONS_REACHED",
            "max_open_positions": 1,
            "current_load": 1,
        },
    )

    result = await approve_candidate_use_case(
        repo,
        DummyKillSwitchClient(),
        execution,
        audit,
        "cand_001",
        123,
        "corr_001",
    )

    assert result["ok"] is False
    assert result["code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["execution_error_code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["execution_error"]["current_load"] == 1
    assert repo.candidate.status == "failed_execution"
    journal_events = [x for x in repo.db.added if isinstance(x, JournalEventModel)]
    assert len(journal_events) == 1
    assert journal_events[0].payload["execution_error_code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert journal_events[0].payload["execution_error"]["max_open_positions"] == 1


@pytest.mark.asyncio
async def test_approve_candidate_journal_insert_failure_keeps_candidate_status_unchanged():
    repo = DummyRepo(DummyCandidate(), db=_FakeDb(fail_journal_flush=True))
    audit = DummyOperatorActionRepo(db=repo.db)
    result = await approve_candidate_use_case(
        repo,
        DummyKillSwitchClient(),
        DummyExecutionClient(ok=False),
        audit,
        "cand_001",
        123,
        "corr_001",
    )
    assert result["ok"] is False
    assert result["code"] == "JOURNAL_WRITE_FAILED"
    assert repo.candidate.status == "approved"
    assert repo.candidate.execution_id is None
    assert len(audit.records) == 1


@pytest.mark.asyncio
async def test_approve_success_writes_candidate_approved_and_journal_event_atomically():
    repo = DummyRepo(DummyCandidate())
    audit = DummyOperatorActionRepo(db=repo.db)
    result = await approve_candidate_use_case(
        repo,
        DummyKillSwitchClient(),
        DummyExecutionClient(execution_id="exe_123"),
        audit,
        "cand_001",
        123,
        "corr_001",
    )
    assert result["ok"] is True
    assert repo.candidate.status == "submitted"
    assert repo.candidate.execution_id == "exe_123"
    assert audit.records[0]["payload_json"]["status"] == "approved"
    journal_events = [x for x in repo.db.added if isinstance(x, JournalEventModel)]
    assert len(journal_events) == 1
    assert journal_events[0].event_type == "candidate_approved"
    assert journal_events[0].payload["candidate_id"] == "cand_001"


@pytest.mark.asyncio
async def test_approve_candidate_expired():
    repo = DummyRepo(DummyCandidate(expired=True))
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), DummyOperatorActionRepo(db=repo.db), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXPIRED"


@pytest.mark.asyncio
async def test_approve_candidate_failed_execution_is_terminal():
    repo = DummyRepo(DummyCandidate(status="failed_execution"))
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), DummyOperatorActionRepo(db=repo.db), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_FAILED"


@pytest.mark.asyncio
async def test_approve_candidate_blocked_when_kill_switch_active():
    repo = DummyRepo(DummyCandidate())
    kill_switch = DummyKillSwitchClient(kill_switch_active=True)
    execution = DummyExecutionClient()
    audit = DummyOperatorActionRepo(db=repo.db)
    result = await approve_candidate_use_case(repo, kill_switch, execution, audit, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "KILL_SWITCH_ACTIVE"
    assert repo.candidate.status == "pending"
    assert getattr(repo.candidate, "execution_id", None) is None
    assert repo.approve_calls == 0
    assert execution.calls == 0
    assert kill_switch.calls == 1
    assert audit.records == []


def test_reject_candidate_success_writes_candidate_and_journal_atomically():
    repo = DummyRepo(DummyCandidate())
    audit = DummyOperatorActionRepo(db=repo.db)
    result = reject_candidate_use_case(repo, audit, "cand_001", 123, "corr_001")
    assert result["ok"] is True
    assert result["code"] == "REJECTED"
    assert repo.candidate.status == "rejected"
    assert len(audit.records) == 1
    journal_events = [x for x in repo.db.added if isinstance(x, JournalEventModel)]
    assert len(journal_events) == 1
    assert journal_events[0].event_type == "candidate_rejected"
    assert journal_events[0].payload["candidate_id"] == "cand_001"


def test_reject_candidate_already_approved():
    repo = DummyRepo(DummyCandidate(status="approved"))
    result = reject_candidate_use_case(repo, DummyOperatorActionRepo(db=repo.db), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "ALREADY_APPROVED"


@pytest.mark.asyncio
async def test_approve_candidate_not_found():
    repo = DummyRepo(None)
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), DummyOperatorActionRepo(db=repo.db), "cand_missing", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "NOT_FOUND"
