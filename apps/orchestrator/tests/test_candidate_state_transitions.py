from datetime import datetime, timedelta, timezone

import httpx
import pytest

from apps.orchestrator.application.approve_candidate import approve_candidate_use_case
from apps.orchestrator.application.create_candidate import create_candidate_use_case
from apps.orchestrator.application.reject_candidate import reject_candidate_use_case
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

    def write(self, payload: dict) -> None:
        self.writes.append(payload)


class FailingJournalClient:
    def write(self, payload: dict) -> None:
        raise RuntimeError("journal host unavailable")


class DummyOperatorActionRepo:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, **kwargs):
        self.records.append(kwargs)
        return kwargs


class DummyCandidate:
    def __init__(self, status: str = "pending", expired: bool = False):
        self.candidate_id = "cand_001"
        self.status = status
        self.execution_payload_json = {"symbol": "BTCUSDT", "side": "buy"}
        self.ttl_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1) if expired else datetime.now(timezone.utc) + timedelta(seconds=120)


class DummyRepo:
    def __init__(self, candidate):
        self.candidate = candidate
        self.marked_failed = False
        self.approve_calls = 0

    def create_candidate(self, **kwargs):
        class Row:
            candidate_id = kwargs["candidate_id"]
            status = "pending"
            ttl_expires_at = kwargs["ttl_expires_at"]
        return Row()

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

    def reject_candidate(self, model, telegram_user_id: int):
        model.status = "rejected"
        return model

    def attach_execution(self, model, execution_id: str):
        model.execution_id = execution_id
        model.status = "submitted"
        return model

    def mark_execution_failed(self, model):
        model.status = "failed_execution"
        model.execution_id = None
        self.marked_failed = True
        return model


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
    journal = DummyJournalClient()
    result = create_candidate_use_case(repo, journal, make_signal(), make_risk(), make_review(True), "corr_001", ttl_seconds=120)
    assert result["ok"] is True
    assert result["code"] == "CANDIDATE_CREATED"
    assert result["journal_write_ok"] is True
    assert result["journal_error"] is None
    assert len(journal.writes) == 1


def test_create_candidate_succeeds_when_journal_write_fails():
    repo = DummyRepo(None)
    result = create_candidate_use_case(
        repo,
        FailingJournalClient(),
        make_signal(),
        make_risk(),
        make_review(True),
        "corr_001",
        ttl_seconds=120,
    )
    assert result["ok"] is True
    assert result["code"] == "CANDIDATE_CREATED"
    assert result["journal_write_ok"] is False
    assert result["journal_error"] == "journal host unavailable"


@pytest.mark.asyncio
async def test_approve_candidate_submits_execution_and_writes_audit_and_journal():
    repo = DummyRepo(DummyCandidate())
    journal = DummyJournalClient()
    audit = DummyOperatorActionRepo()
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), audit, journal, "cand_001", 123, "corr_001")
    assert result["ok"] is True
    assert result["execution_id"] == "exe_001"
    assert len(audit.records) == 1
    assert len(journal.writes) == 1


@pytest.mark.asyncio
async def test_approve_candidate_missing_execution_id_writes_failure_journal():
    repo = DummyRepo(DummyCandidate())
    journal = DummyJournalClient()
    audit = DummyOperatorActionRepo()
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(execution_id=None), audit, journal, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_SUBMISSION_NO_ID"
    assert repo.candidate.status == "failed_execution"
    assert repo.candidate.execution_id is None
    assert repo.marked_failed is True
    assert len(audit.records) == 1
    assert len(journal.writes) == 1
    assert journal.writes[0]["event_type"] == "execution_failed_after_approval"


@pytest.mark.asyncio
async def test_approve_candidate_execution_not_accepted_rolls_back_candidate():
    repo = DummyRepo(DummyCandidate())
    journal = DummyJournalClient()
    audit = DummyOperatorActionRepo()
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(ok=False), audit, journal, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_REJECTED"
    assert result["execution_error_code"] == "EXECUTION_REJECTED"
    assert result["execution_error"]["code"] == "EXECUTION_REJECTED"
    assert repo.candidate.status == "failed_execution"
    assert repo.candidate.execution_id is None
    assert len(audit.records) == 1
    assert len(journal.writes) == 1
    assert journal.writes[0]["event_type"] == "execution_failed_after_approval"
    assert journal.writes[0]["payload"]["execution_error_code"] == "EXECUTION_REJECTED"


@pytest.mark.asyncio
async def test_approve_candidate_execution_http_error_rolls_back_candidate():
    repo = DummyRepo(DummyCandidate())
    journal = DummyJournalClient()
    audit = DummyOperatorActionRepo()
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(raises=True), audit, journal, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_REQUEST_FAILED"
    assert result["execution_error_code"] == "EXECUTION_REQUEST_FAILED"
    assert result["execution_error"]["code"] == "EXECUTION_REQUEST_FAILED"
    assert repo.candidate.status == "failed_execution"
    assert repo.candidate.execution_id is None
    assert len(audit.records) == 1
    assert len(journal.writes) == 1
    assert journal.writes[0]["event_type"] == "execution_failed_after_approval"
    assert journal.writes[0]["payload"]["execution_error_code"] == "EXECUTION_REQUEST_FAILED"


@pytest.mark.asyncio
async def test_approve_candidate_propagates_max_open_reject_reason():
    repo = DummyRepo(DummyCandidate())
    journal = DummyJournalClient()
    audit = DummyOperatorActionRepo()
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
        journal,
        "cand_001",
        123,
        "corr_001",
    )

    assert result["ok"] is False
    assert result["code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["execution_error_code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert result["execution_error"]["current_load"] == 1
    assert repo.candidate.status == "failed_execution"
    assert len(journal.writes) == 1
    assert journal.writes[0]["payload"]["execution_error_code"] == "MAX_OPEN_POSITIONS_REACHED"
    assert journal.writes[0]["payload"]["execution_error"]["max_open_positions"] == 1


@pytest.mark.asyncio
async def test_approve_candidate_expired():
    repo = DummyRepo(DummyCandidate(expired=True))
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), DummyOperatorActionRepo(), DummyJournalClient(), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXPIRED"


@pytest.mark.asyncio
async def test_approve_candidate_failed_execution_is_terminal():
    repo = DummyRepo(DummyCandidate(status="failed_execution"))
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), DummyOperatorActionRepo(), DummyJournalClient(), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "EXECUTION_FAILED"


@pytest.mark.asyncio
async def test_approve_candidate_blocked_when_kill_switch_active():
    repo = DummyRepo(DummyCandidate())
    kill_switch = DummyKillSwitchClient(kill_switch_active=True)
    execution = DummyExecutionClient()
    audit = DummyOperatorActionRepo()
    journal = DummyJournalClient()
    result = await approve_candidate_use_case(repo, kill_switch, execution, audit, journal, "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "KILL_SWITCH_ACTIVE"
    assert repo.candidate.status == "pending"
    assert getattr(repo.candidate, "execution_id", None) is None
    assert repo.approve_calls == 0
    assert execution.calls == 0
    assert kill_switch.calls == 1
    assert audit.records == []
    assert journal.writes == []


def test_reject_candidate_already_approved():
    repo = DummyRepo(DummyCandidate(status="approved"))
    result = reject_candidate_use_case(repo, DummyOperatorActionRepo(), DummyJournalClient(), "cand_001", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "ALREADY_APPROVED"


@pytest.mark.asyncio
async def test_approve_candidate_not_found():
    repo = DummyRepo(None)
    result = await approve_candidate_use_case(repo, DummyKillSwitchClient(), DummyExecutionClient(), DummyOperatorActionRepo(), DummyJournalClient(), "cand_missing", 123, "corr_001")
    assert result["ok"] is False
    assert result["code"] == "NOT_FOUND"
